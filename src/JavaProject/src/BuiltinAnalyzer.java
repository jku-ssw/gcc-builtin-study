import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class BuiltinAnalyzer {

	private static final String PROJECTS = "../projects";

	public static void main(String[] args) throws Exception {
		new BuiltinAnalyzer().start();
	}

	private static final int LIMIT = 6000;
	private final AtomicInteger processedLines = new AtomicInteger(0);
	final static Connection connection;
	final static Pattern builtinSearchPattern;
	final static ConcurrentHashMap<String, Integer> builtinNames;
	final static Pattern inlineAssemblyPattern;
	private static final boolean PROCESS_GCC = true;

	static {
		try {
			connection = DriverManager.getConnection("jdbc:sqlite:../../database.db?journal_mode=WAL");
			connection.setAutoCommit(false);
			builtinNames = getBuiltinNamesToBuiltinIdMapping();
			String ordBuiltinNames = builtinNames.keySet().stream()
					.filter(s -> !s.startsWith("__builtin_") || s.startsWith("__builtin__"))
					.collect(Collectors.joining("|"));
			String regexString = "(?<![a-zA-Z0-9_])(" + ordBuiltinNames
					+ "|__builtin_[a-zA-Z0-9][a-zA-Z0-9_]*)(?![a-zA-Z0-9_])";
			String inlineAssemblyString = "(?<![a-zA-Z0-9_])(__asm__|asm)(?![a-zA-Z0-9_])";
			inlineAssemblyPattern = Pattern.compile(inlineAssemblyString);
			builtinSearchPattern = Pattern.compile(regexString);
		} catch (Exception e) {
			throw new AssertionError(e);
		}
	}

	private void start() throws SQLException, IOException {

		Map<Path, Integer> projectPaths = getProjectPathsToProjectIdMapping();
		Instant start = Instant.now();
		if (PROCESS_GCC) {
			Path gccPath = Paths.get(PROJECTS, "gcc-mirror-gcc");
			if (!gccPath.toFile().exists()) {
				throw new FileNotFoundException("expected that GCC was downloaded");
			}
			Files.walk(gccPath).filter(f -> isInterestingFile(f)).collect(Collectors.toList()).forEach(file -> {
				try (final BufferedReader reader = new BufferedReader(new FileReader(file.toString()))) {
					while (reader.ready()) {
						String line = reader.readLine();
						Matcher matcher = builtinSearchPattern.matcher(line);
						while (matcher.find() && !builtinNames.containsKey(matcher.group(1))) {
							System.out.println(matcher.group(1));
							PreparedStatement newBuiltin = connection.prepareStatement(
									"INSERT INTO BuiltinsUnfiltered(BUILTIN_NAME, BUILTIN_CATEGORY, DOCUMENTATION_URL, DOCUMENTATION_SECTION_HEADER, MACHINE_SPECIFIC, FROM_DEF) VALUES(?, 'GCC internal', '-', 'Internal GCC builtins', 0, 0)");
							newBuiltin.setString(1, matcher.group(1));
							// should always succeed because we are in a
							// synchronized method
							newBuiltin.executeUpdate();
							newBuiltin.close();
							connection.commit();

							builtinNames.put(matcher.group(1), getBuiltinId(matcher.group(1)));
						}
					}
				} catch (Exception e) {
					throw new AssertionError(e);
				}
			});
		}
		projectPaths.keySet().parallelStream().forEach(path -> {
			int id = projectPaths.get(path);
			AtomicBoolean isFreestanding = new AtomicBoolean(false);
			AtomicBoolean containsNoBuiltin = new AtomicBoolean(false);
			AtomicBoolean containsMakefile = new AtomicBoolean(false);
			AtomicInteger nrInlineAssemblyFragments = new AtomicInteger(0);
			try {
				final PreparedStatement insertBuiltin = connection.prepareStatement(
						"insert into BuiltinsInGithubProjectUnfiltered(GITHUB_PROJECT_ID, FILE_PATH, LINE_NR, CODE_FRAGMENT, BUILTIN_ID) VALUES(?, ?, ?, ?, ?)");
				Files.walk(path).filter(f -> isInterestingFile(f)).collect(Collectors.toList()).forEach(file -> {
					try {
						if (isCFile(file)) {
							try (final BufferedReader reader = new BufferedReader(new FileReader(file.toString()))) {
								int lineNr = 1;
								while (reader.ready()) {
									String line = reader.readLine();
									Matcher inlineAssemblyMatcher = inlineAssemblyPattern.matcher(line);
									while (inlineAssemblyMatcher.find()) {
										nrInlineAssemblyFragments.incrementAndGet();
									}
									Matcher matcher = builtinSearchPattern.matcher(line);
									while (matcher.find()) {
										insertBuiltin.setInt(1, id);
										Path projectPath = Paths.get(PROJECTS).toAbsolutePath().normalize();
										String relativePath = projectPath.relativize(file.toAbsolutePath().normalize())
												.toString();
										insertBuiltin.setString(2, relativePath);
										insertBuiltin.setInt(3, lineNr);
										insertBuiltin.setString(4, line);
										String builtin = matcher.group(1);
										Integer builtinId = builtinNames.get(builtin);
										if (builtinId == null) {
											builtinId = insertNewBuiltinAndGetId(builtin, builtinNames);
										}
										insertBuiltin.setInt(5, builtinId);
										insertBuiltin.addBatch();
									}
									lineNr++;
								}
								processedLines.addAndGet(lineNr);
							}
						} else if (isMakefile(file)) {
							containsMakefile.set(true);
							try (final BufferedReader reader = new BufferedReader(new FileReader(file.toString()))) {
								while (reader.ready()) {
									String line = reader.readLine();
									if (line.contains("-ffreestanding")) {
										isFreestanding.set(true);
									}
									if (line.contains("-fno-builtin")) {
										containsNoBuiltin.set(true);
									}
								}
							}
						}
					} catch (FileNotFoundException e) {
						e.printStackTrace();
						// invalid symbolic link
					} catch (Exception e) {
						throw new AssertionError(e);
					}
				});
				insertBuiltin.executeBatch();
				PreparedStatement setProcessed = connection.prepareStatement(
						"update GithubProjectUnfiltered SET PROCESSED=1, CONTAINS_MAKEFILE=?, MAKEFILE_CONTAINS_FREESTANDING=?, MAKEFILE_CONTAINS_NO_PLUGIN=?, NR_INLINE_ASSEMBLY_FRAGMENT=? WHERE ID=?");
				setProcessed.setInt(1, containsMakefile.get() ? 1 : 0);
				setProcessed.setInt(2, isFreestanding.get() ? 1 : 0);
				setProcessed.setInt(3, containsNoBuiltin.get() ? 1 : 0);
				setProcessed.setInt(4, nrInlineAssemblyFragments.get());
				setProcessed.setInt(5, id);
				//System.out.println("finished processing project " + id);
				setProcessed.executeUpdate();
				setProcessed.close();
				try {
					connection.commit();
				} catch (Exception e) {
					// ignore
				}
			} catch (Exception e) {
				e.printStackTrace();
			}
		});

		Instant end = Instant.now();
		Duration duration = Duration.between(start, end);
		System.out.println("total processing time: " + duration + " LOC: " + processedLines.get());
		System.out.println("LOC per second: " + processedLines.get() / duration.getSeconds());
	}

	static synchronized Integer insertNewBuiltinAndGetId(String builtin, Map<String, Integer> builtinNames)
			throws SQLException {
		Integer builtinId = builtinNames.get(builtin);
		if (builtinId != null) {
			return builtinId;
		}
		// we have encountered an unknown __builtin
		System.out.println("new builtin: " + builtin);
		PreparedStatement newBuiltin = connection.prepareStatement(
				"INSERT INTO BuiltinsUnfiltered(BUILTIN_NAME, BUILTIN_CATEGORY, DOCUMENTATION_URL, DOCUMENTATION_SECTION_HEADER, MACHINE_SPECIFIC, FROM_DEF) VALUES(?, 'Unknown', '-', '-', 0, 0)");
		newBuiltin.setString(1, builtin);
		// should always succeed because we are in a synchronized method
		newBuiltin.executeUpdate();
		newBuiltin.close();
		connection.commit();
		builtinId = getBuiltinId(builtin);
		builtinNames.put(builtin, builtinId);
		return builtinId;
	}

	static Integer getBuiltinId(String builtin) throws SQLException {
		Integer builtinId;
		PreparedStatement getBuiltinId = connection
				.prepareStatement("SELECT ID FROM BuiltinsUnfiltered WHERE BUILTIN_NAME=?");
		getBuiltinId.setString(1, builtin);
		ResultSet rs = getBuiltinId.executeQuery();
		rs.next();
		builtinId = rs.getInt("ID");
		return builtinId;
	}

	private Map<Path, Integer> getProjectPathsToProjectIdMapping() throws SQLException {
		ConcurrentHashMap<Path, Integer> projectPaths = new ConcurrentHashMap<>();
		try (Statement s = connection.createStatement()) {
			ResultSet rs = s.executeQuery("SELECT * FROM GithubProjectUnfiltered WHERE PROCESSED = 0 LIMIT " + LIMIT);
			while (rs.next()) {
				String owner = rs.getString("GITHUB_OWNER_NAME");
				String project = rs.getString("GITHUB_PROJECT_NAME");
				int id = rs.getInt("ID");
				Path path = Paths.get(PROJECTS, owner + "-" + project).toAbsolutePath().normalize();
				projectPaths.put(path, id);
			}
		}
		return projectPaths;
	}

	private static ConcurrentHashMap<String, Integer> getBuiltinNamesToBuiltinIdMapping() throws SQLException {
		ConcurrentHashMap<String, Integer> builtinNames = new ConcurrentHashMap<>();
		try (Statement s = connection.createStatement()) {
			ResultSet rs = s.executeQuery("SELECT * FROM BuiltinsUnfiltered");
			while (rs.next()) {
				int id = rs.getInt("ID");
				String name = rs.getString("BUILTIN_NAME");
				builtinNames.put(name, id);
			}
		}
		return builtinNames;
	}

	public static boolean isInterestingFile(Path file) {
		return Files.isReadable(file) && (isMakefile(file) || isCFile(file));
	}

	private static boolean isMakefile(Path file) {
		if (file.toFile().isDirectory()) {
			return false;
		}
		String name = file.toFile().getName();
		return name.equalsIgnoreCase("makefile");
	}

	public static boolean isCFile(Path file) {
		if (file.toFile().isDirectory()) {
			return false;
		}
		String name = file.toFile().getName().toLowerCase();
		return name.endsWith(".c") || name.endsWith(".h");
	}

}
