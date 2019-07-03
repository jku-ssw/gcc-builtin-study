import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.regex.Matcher;
import java.util.stream.IntStream;

import org.eclipse.jgit.api.Git;
import org.eclipse.jgit.diff.DiffEntry;
import org.eclipse.jgit.diff.DiffFormatter;
import org.eclipse.jgit.diff.RawTextComparator;
import org.eclipse.jgit.errors.AmbiguousObjectException;
import org.eclipse.jgit.errors.CorruptObjectException;
import org.eclipse.jgit.errors.IncorrectObjectTypeException;
import org.eclipse.jgit.errors.MissingObjectException;
import org.eclipse.jgit.lib.AnyObjectId;
import org.eclipse.jgit.lib.Constants;
import org.eclipse.jgit.lib.ObjectReader;
import org.eclipse.jgit.lib.PersonIdent;
import org.eclipse.jgit.lib.Repository;
import org.eclipse.jgit.revwalk.RevCommit;
import org.eclipse.jgit.revwalk.RevWalk;
import org.eclipse.jgit.storage.file.FileRepositoryBuilder;
import org.eclipse.jgit.treewalk.AbstractTreeIterator;
import org.eclipse.jgit.treewalk.CanonicalTreeParser;
import org.eclipse.jgit.treewalk.EmptyTreeIterator;
import org.eclipse.jgit.util.io.DisabledOutputStream;

public class HistoryAnalyzer {

	static final int LIMIT = 5000;
	static String query = "SELECT ID, GITHUB_OWNER_NAME, GITHUB_PROJECT_NAME, GITHUB_URL, (CLOC_LOC_C + CLOC_LOC_H)/1000 AS LOC, count FROM DistinctBuiltinCountPerProject WHERE CHECKED_HISTORY IS NOT \"1\" ORDER BY CLOC ASC LIMIT ?";
	static final boolean UPDATE_RESULTS = true;

	public static void main(String[] args) throws Exception {
		try (Statement stmt = BuiltinAnalyzer.connection.createStatement()) {
			if (UPDATE_RESULTS) {
				String projectIdsPartiallyProcessedQuery = "SELECT DISTINCT GITHUB_PROJECT_ID FROM CommitHistoryUnfiltered LEFT JOIN GithubProject ON CommitHistoryUnfiltered.GITHUB_PROJECT_ID = GithubProject.ID WHERE GithubProject.CHECKED_HISTORY IS NOT \"1\"";
				PreparedStatement ps = BuiltinAnalyzer.connection.prepareStatement(projectIdsPartiallyProcessedQuery);
				ResultSet rs = ps.executeQuery();
				StringBuilder sb = new StringBuilder();
				int i = 0;
				sb.append('(');
				while (rs.next()) {
					if (i++ != 0) { 
						sb.append(", ");
					}
					sb.append(rs.getString("GITHUB_PROJECT_ID"));
				}
				sb.append(')');
				String projectIdsPartiallyProcessed = sb.toString();
				stmt.executeUpdate("DELETE FROM CommitHistoryUnfiltered WHERE CommitHistoryUnfiltered.GITHUB_PROJECT_ID IN " + projectIdsPartiallyProcessed);
				stmt.executeUpdate("DELETE FROM CommitHistoryDiffEntryUnfiltered WHERE CommitHistoryDiffEntryUnfiltered.GITHUB_PROJECT_ID IN " + projectIdsPartiallyProcessed);
			} else {
				stmt.executeUpdate("UPDATE GithubProjectUnfiltered SET CHECKED_HISTORY=NULL");
				stmt.executeUpdate("DELETE FROM CommitHistoryUnfiltered");
				stmt.executeUpdate("DELETE FROM CommitHistoryDiffEntryUnfiltered");
			}
		}

		PreparedStatement getBuiltinId = BuiltinAnalyzer.connection.prepareStatement(query);
		getBuiltinId.setInt(1, LIMIT);
		ResultSet rs = getBuiltinId.executeQuery();
		List<Integer> projectIds = new ArrayList<>();
		List<String> projectPaths = new ArrayList<>();
		while (rs.next()) {
			int projectId = rs.getInt("ID");
			String ownerName = rs.getString("GITHUB_OWNER_NAME");
			String projectName = rs.getString("GITHUB_PROJECT_NAME");
			projectIds.add(projectId);
			projectPaths.add(String.format("../projects/%s-%s/.git", ownerName, projectName));
		}
		IntStream.range(0, projectIds.size()).parallel().forEach(j -> {
			try {
				int projectId = projectIds.get(j);
				new HistoryAnalyzer(projectId, projectPaths.get(j)).processRepository(new FileRepositoryBuilder());
				setProcessed(projectId);
			} catch (Exception e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		});

	}

	private static void setProcessed(int projectId) throws SQLException {
		PreparedStatement setProcessed = BuiltinAnalyzer.connection
				.prepareStatement("update GithubProjectUnfiltered SET CHECKED_HISTORY=1 WHERE ID=?");
		setProcessed.setInt(1, projectId);
		System.out.println("finished processing");
		commit(setProcessed);
	}

	static class CommitInfo {
		final String message;
		final int commitTime;
		final Date time;
		final String committerName;
		final String hash;
		final String committerEmail;

		public CommitInfo(String message, int commitTime, Date time, String committerName, String committerEmail,
				String hash) {
			this.message = message;
			this.commitTime = commitTime;
			this.time = time;
			this.committerName = committerName;
			this.hash = hash;
			this.committerEmail = committerEmail;
		}
	}

	private int githubId;
	private String projectPath;

	public HistoryAnalyzer(int githubId, String projectPath) {
		this.githubId = githubId;
		this.projectPath = projectPath;
	}

	/**
	 * Did we already insert the current commit? We only want to if the commit
	 * modifies the builtin usage.
	 */
	boolean insertedCommit;

	int currentCommitSequenceNumber;

	private void processRepository(FileRepositoryBuilder builder) throws Exception {
		Repository repo = builder.setGitDir(new File(projectPath).getAbsoluteFile().getCanonicalFile())
				.setMustExist(true).build();
		Git git = new Git(repo);
		List<RevCommit> commits = getCommits(repo);
		for (RevCommit commit : commits) {
			currentCommitSequenceNumber++;
			CommitInfo commitInfo = getCommitInfo(commit);
			insertedCommit = false;
			DiffFormatter df = new DiffFormatter(DisabledOutputStream.INSTANCE);
			df.setRepository(repo);
			df.setDiffComparator(RawTextComparator.DEFAULT);
			df.setDetectRenames(false);
			ObjectReader reader = repo.newObjectReader();
			AbstractTreeIterator referenceTree;
			if (commit.getParents().length == 0) {
				referenceTree = new EmptyTreeIterator();
			} else {
				RevCommit parent = commit.getParent(0);
				referenceTree = new CanonicalTreeParser(null, reader, parent.getTree());
			}
			CanonicalTreeParser currentCommitTree = new CanonicalTreeParser(null, reader, commit.getTree());
			List<DiffEntry> diffs = df.scan(referenceTree, currentCommitTree);
			for (DiffEntry diff : diffs) {
				ByteArrayOutputStream os = new ByteArrayOutputStream();
				try (DiffFormatter formatter = new DiffFormatter(os)) {
					formatter.setRepository(repo);
					switch (diff.getChangeType()) {
					case ADD:
						if (BuiltinAnalyzer.isCFile(new File(diff.getNewPath()).toPath())) {
							formatter.format(diff);
							String[] diffOutput = os.toString().split("\n");
							int line = 0;
							for (String diffLine : diffOutput) {
								Matcher m = BuiltinAnalyzer.builtinSearchPattern.matcher(diffLine);
								while (m.find()) {
									insertBuiltinUsage("add-file", commitInfo, diff.getNewPath(), diffLine.substring(1),
											line, formatter, diff, 1, m);
								}
								line++;
							}
						}
						break;
					case MODIFY:
						if (BuiltinAnalyzer.isCFile(new File(diff.getNewPath()).toPath())) {
							formatter.format(diff);
							String[] diffOutput = os.toString().split("\n");
							int line = 0;
							for (String diffLine : diffOutput) {
								Matcher m = BuiltinAnalyzer.builtinSearchPattern.matcher(diffLine);
								while (m.find()) {
									if (diffLine.startsWith("-")) {
										insertBuiltinUsage("modify-delete", commitInfo, diff.getNewPath(),
												diffLine.substring(1), line, formatter, diff, -1, m);
									} else if (diffLine.startsWith("+")) {
										insertBuiltinUsage("modify-add", commitInfo, diff.getOldPath(),
												diffLine.substring(1), line, formatter, diff, 1, m);
									}
								}
								line++;
							}
						}
						break;
					case DELETE:
						if (BuiltinAnalyzer.isCFile(new File(diff.getOldPath()).toPath())) {
							formatter.format(diff);
							String[] diffOutput = os.toString().split("\n");
							int line = 0;
							for (String diffLine : diffOutput) {
								Matcher m = BuiltinAnalyzer.builtinSearchPattern.matcher(diffLine);
								while (m.find()) {
									insertBuiltinUsage("delete-file", commitInfo, diff.getOldPath(),
											diffLine.substring(1), line, formatter, diff, -1, m);
								}
								line++;
							}
						}
						break;
					case COPY:
						throw new AssertionError(os.toString());
					case RENAME:
						throw new AssertionError("setDetectRenames(false)");
					}
				}
			}

			df.close();
		}
		git.close();
	}

	private List<RevCommit> getCommits(Repository repo)
			throws AmbiguousObjectException, IncorrectObjectTypeException, IOException, MissingObjectException {
		// get commits
		try (RevWalk walk = new RevWalk(repo)) {
			AnyObjectId headId;
			headId = repo.resolve(Constants.HEAD);
			RevCommit root = walk.parseCommit(headId);
			if (root == null) {
				throw new AssertionError();
			}
			List<RevCommit> commits = new ArrayList<>();
			RevCommit cur = root;
			commits.add(cur);
			while (cur.getParentCount() > 0) {
				cur = cur.getParent(0);
				walk.parseCommit(cur);
				commits.add(cur);
			}
			return commits;
		}
	}

	private CommitInfo getCommitInfo(RevCommit commit) {
		String message = commit.getFullMessage();
		int commitTime = commit.getCommitTime();
		String hash = commit.getName();
		java.util.Date time = new java.util.Date((long) commitTime * 1000);
		PersonIdent authorIdent = commit.getAuthorIdent();
		String commitName = authorIdent.getName();
		String committerEmailAddress = authorIdent.getEmailAddress();
		CommitInfo commitInfo = new CommitInfo(message, commitTime, time, commitName, committerEmailAddress, hash);
		return commitInfo;
	}

	private void insertBuiltinUsage(String event, CommitInfo commitInfo, String path, String builtinLine, int lineNr,
			DiffFormatter df, DiffEntry diff, int modification, Matcher matcher)
			throws CorruptObjectException, MissingObjectException, IOException, SQLException {
		if (!insertedCommit) {
			PreparedStatement newCommit = BuiltinAnalyzer.connection
					.prepareStatement("INSERT INTO CommitHistoryUnfiltered(" + "GITHUB_PROJECT_ID," + "COMMIT_MESSAGE,"
							+ "COMMIT_TIME_UNIX," + "COMMIT_DATE," + "COMMITTER_NAME," + "COMMITTER_EMAIL,"
							+ "COMMIT_HASH, COMMIT_NR)" + "VALUES(" + "?, ?, ?, ?, ?, ?, ?, ?)");
			newCommit.setInt(1, githubId);
			newCommit.setString(2, commitInfo.message);
			newCommit.setInt(3, commitInfo.commitTime);
			newCommit.setString(4, commitInfo.time.toString());
			newCommit.setString(5, commitInfo.committerName);
			newCommit.setString(6, commitInfo.committerEmail);
			newCommit.setString(7, commitInfo.hash);
			newCommit.setInt(8, currentCommitSequenceNumber);
			commit(newCommit);
			insertedCommit = true;
		}

		PreparedStatement newBuiltin = BuiltinAnalyzer.connection.prepareStatement(
				"INSERT INTO CommitHistoryDiffEntryUnfiltered(COMMIT_HASH," + "EVENT_TYPE," + "FILE_PATH,"
						+ "NR_BUILTIN_CHANGE," + "LINE_WITH_BUILTIN," + "BUILTIN_LINE_NR, BUILTIN_ID, GITHUB_PROJECT_ID"
						+ ")" + "VALUES(" + "?, ?, ?, ?, ?, ?, ?, ?)");
		newBuiltin.setString(1, commitInfo.hash);
		newBuiltin.setString(2, event);
		newBuiltin.setString(3, path);
		newBuiltin.setInt(4, modification);
		newBuiltin.setString(5, builtinLine);
		newBuiltin.setInt(6, lineNr);
		String builtin = matcher.group(1);
		Integer builtinId = BuiltinAnalyzer.builtinNames.get(builtin);
		if (builtinId == null) {
			builtinId = BuiltinAnalyzer.insertNewBuiltinAndGetId(builtin, BuiltinAnalyzer.builtinNames);
		}
		newBuiltin.setInt(7, builtinId);
		newBuiltin.setInt(8, githubId);
		commit(newBuiltin);
	}

	private static void commit(PreparedStatement statement) throws SQLException {
		statement.executeUpdate();
		statement.close();
		try {
			BuiltinAnalyzer.connection.commit();
		} catch (Exception e) {

		}
	}

}
