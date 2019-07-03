import java.io.File;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;


class GitHubProject {
	
	static final File PLOT_DIRECTORY = new File("../../generated/historical-data/plots/png");
	
	static void addRsAsGithubProjects(List<GitHubProject> projectList, ResultSet rs) throws SQLException {
		while (rs.next()) {
			int projectId = rs.getInt(1);
			String projectName = rs.getString(2);
			String trend = rs.getString(3);
			projectList.add(new GitHubProject(projectId, projectName, trend));
		}
	}

	int id;
	String projectName;
	String trend;
	ImageFile imageFile;

	private boolean queriedImageFile;

	
	public GitHubProject(int projectId, String projectName, String trend) {
		this.id = projectId;
		this.projectName = projectName;
		this.trend = trend;
	}

	@Override
	public String toString() {
		if (trend == null) {
			return String.format("%s (%d)", projectName, id);
		} else {
			return String.format("%s [%s] (%d)", projectName, trend, id);
		}
	}

	public ImageFile getImageFile() {
		if (!queriedImageFile) {
			Optional<File> optionalImageFile = Arrays.stream(PLOT_DIRECTORY.listFiles())
					.filter(s -> s.getName().startsWith(Integer.toString(id)) && s.getName().contains(projectName) && s.getName().endsWith(".png"))
					.findAny();
			if (optionalImageFile.isPresent()) {
				this.imageFile = new ImageFile(optionalImageFile.get());
			}
			queriedImageFile = true;
		}
		return imageFile;
	}
	
}
