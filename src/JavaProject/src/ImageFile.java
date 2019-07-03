import java.io.File;
import java.sql.ResultSet;
import java.sql.Statement;

class ImageFile {
	File path;
	int projectId;

	public ImageFile(File path) {
		projectId = Integer.parseInt(path.getName().split("-")[0]);
		this.path = path;
	}

	@Override
	public String toString() {
		return path.toString();
	}

	boolean hasBeenProcessed() {
		try {
			Statement s = BuiltinAnalyzer.connection.createStatement();
			ResultSet rs = s.executeQuery(
					"SELECT COUNT(*) FROM BuiltinTrendInGithubProjectUnfiltered WHERE GITHUB_PROJECT_ID =  "
							+ projectId);
			return rs.getInt(1) == 1;
		} catch (Exception e) {
			throw new AssertionError(e);
		}
	}

}