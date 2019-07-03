
import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.GridLayout;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JList;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;
import javax.swing.event.TableModelListener;
import javax.swing.table.TableModel;

public class HistoryBrowser {

	static ImagePanel imagePanel = new ImagePanel();
	
	static String filterString = "";
	private static JList<GitHubProject> projectList;
	private static GitHubProject selectedProject;
	private static JTable commitTable;
	private static JTable builtinTable;
	private static String selectedCommitHash;
	private static JTextArea textField = new JTextArea();
	private static JTextField userName = new JTextField(20);

	public HistoryBrowser() {
		textField.setLineWrap(false);
	}

	public static List<GitHubProject> getProjectList() throws SQLException {
		List<GitHubProject> projectList = new ArrayList<GitHubProject>();
		ResultSet rs;
		String filterByUsername;
		if (userName.getText().isEmpty()) {
			filterByUsername = "";
		} else {
			filterByUsername = " AND USER = '" + userName.getText() + "'";
		}

		if (filterString.equals("")) {

			// unclassified
			String sql = "SELECT ID, GITHUB_PROJECT_NAME, \"unclassified\" FROM GithubProject WHERE GithubProject.CHECKED_HISTORY IS 1 AND ID NOT IN (SELECT GITHUB_PROJECT_ID FROM BuiltinTrendInGithubProjectUnfiltered WHERE 1=1 "
					+ filterByUsername + " OR USER='automatic') " + projectFilter;
			Statement s = BuiltinAnalyzer.connection.createStatement();
			rs = s.executeQuery(sql);
			GitHubProject.addRsAsGithubProjects(projectList, rs);

			s = BuiltinAnalyzer.connection.createStatement();
			sql = "SELECT ID, GITHUB_PROJECT_NAME, TREND FROM GithubProject INNER JOIN BuiltinTrendInGithubProjectUnfiltered history ON GithubProject.ID = history.GITHUB_PROJECT_ID WHERE GithubProject.CHECKED_HISTORY IS 1 "
					+ filterByUsername + projectFilter + " ORDER BY TREND";
			rs = s.executeQuery(sql);
		} else {
			PreparedStatement s = BuiltinAnalyzer.connection.prepareStatement(
					"SELECT ID, GITHUB_PROJECT_NAME, TREND FROM GithubProject LEFT JOIN BuiltinTrendInGithubProjectUnfiltered history ON GithubProject.ID = history.GITHUB_PROJECT_ID WHERE GithubProject.CHECKED_HISTORY IS 1 "
							+ filterByUsername + " AND TREND = ?" + projectFilter + "  ORDER BY TREND");
			s.setString(1, filterString);
			rs = s.executeQuery();
		}

		GitHubProject.addRsAsGithubProjects(projectList, rs);
		return projectList;
	}

	

	public static void main(String[] args) throws Exception {
		JFrame frame = new JFrame("");
		JComponent projectList = getProjectListPanel();
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		JPanel leftPanel = new JPanel();
		leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
		JComboBox<String> projectFilterComboBox = getProjectScopeComboBox();
		projectFilterComboBox.setMaximumSize(new Dimension(projectFilterComboBox.getMaximumSize().width, 10));
		JComboBox<String> comboBox = getFilterComboBox();
		comboBox.setMaximumSize(new Dimension(comboBox.getMaximumSize().width, 10));
		leftPanel.add(projectFilterComboBox);
		leftPanel.add(comboBox);
		leftPanel.add(projectList);
		frame.getContentPane().add(leftPanel, BorderLayout.WEST);
		commitTable = new JTable();
		// set TableCellRenderer into a specified JTable column class
		commitTable.getSelectionModel().addListSelectionListener(new ListSelectionListener() {

			@Override
			public void valueChanged(ListSelectionEvent e) {
				selectedCommitHash = (String) commitTable.getValueAt(commitTable.getSelectedRow(), 4);
				textField.setText((String) commitTable.getValueAt(commitTable.getSelectedRow(), 1));
				updateBuiltinTable();
			}
		});
		JScrollPane scrollPane = new JScrollPane(commitTable);
		updateCommitTable();

		builtinTable = new JTable();
		JScrollPane scrollPaneBuiltins = new JScrollPane(builtinTable);

		JPanel rightPanel = new JPanel();
		rightPanel.setLayout(new GridLayout(2, 3));
		rightPanel.add(textField);
		rightPanel.add(scrollPaneBuiltins);

		userName.setMaximumSize(new Dimension(100, 30));
		userName.addKeyListener(new KeyListener() {

			@Override
			public void keyTyped(KeyEvent e) {
				updateProjectList();
			}

			@Override
			public void keyReleased(KeyEvent e) {
			}

			@Override
			public void keyPressed(KeyEvent e) {
			}
		});
		ActionListener buttonListener = new ActionListener() {

			@Override
			public void actionPerformed(ActionEvent e) {
				if (userName.getText().isEmpty()) {
					JOptionPane.showMessageDialog(null, "Please enter your user name", "Missing user name",
							JOptionPane.ERROR_MESSAGE);
				} else {
					try {
						PreparedStatement newClassification = BuiltinAnalyzer.connection.prepareStatement(
								"INSERT OR REPLACE INTO BuiltinTrendInGithubProjectUnfiltered(GITHUB_PROJECT_ID, TREND, USER) VALUES(?, ?, ?)");
						newClassification.setInt(1, selectedProject.id);
						newClassification.setString(2, ((JButton) e.getSource()).getText());
						newClassification.setString(3, userName.getText());
						newClassification.executeUpdate();
						newClassification.close();
						BuiltinAnalyzer.connection.commit();
						updateProjectList();
						HistoryBrowser.projectList.setSelectedIndex(0);
					} catch (Exception exc) {
						throw new AssertionError(exc);
					}
				}
			}
		};

//		addButton(scrollPane, buttonListener, "onset");
		JPanel buttonPanel = new JPanel();
		buttonPanel.setLayout(new BoxLayout(buttonPanel, BoxLayout.Y_AXIS));
		buttonPanel.add(userName);
		addButton(buttonPanel, buttonListener, "increasing, then decreasing");
//		addButton(scrollPane, buttonListener, "decreasing, then increasing");
//		addButton(scrollPane, buttonListener, "decreasing, then stable");
		addButton(buttonPanel, buttonListener, "mostly increasing");
//		addButton(scrollPane, buttonListener, "mostly decreasing");
//		addButton(scrollPane, buttonListener, "decreasing, then stable");
		addButton(buttonPanel, buttonListener, "increasing, then stable");
		addButton(buttonPanel, buttonListener, "mostly stable");
		addButton(buttonPanel, buttonListener, "stable, then increasing");
		addButton(buttonPanel, buttonListener, "spike, then stable");
		addButton(buttonPanel, buttonListener, "no clear pattern");
		addButton(buttonPanel, buttonListener, "not yet decided");
		addButton(buttonPanel, buttonListener, "initial import");
//		JPanel textPanel = new JPanel(new FlowLayout());
//		mainPanel.add(userName);

		JPanel mainPanel = new JPanel();
		mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
		mainPanel.add(imagePanel);

		mainPanel.add(buttonPanel);
		mainPanel.add(scrollPane);
		frame.getContentPane().add(mainPanel, BorderLayout.CENTER);

		frame.getContentPane().add(rightPanel, BorderLayout.EAST);
		scrollPane.setMaximumSize(new Dimension(mainPanel.getMaximumSize().width, 300));
		frame.pack();
		Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
		frame.setSize(d);
		frame.setVisible(true);
	}

	static void addButton(JComponent buttonPanel, ActionListener buttonListener, String text) {
		JButton mostlyIncreasing = new JButton(text);
		mostlyIncreasing.addActionListener(buttonListener);
		buttonPanel.add(mostlyIncreasing);
	}

	private static void updateBuiltinTable() {
		if (selectedProject != null) {
			try {
				String query = "SELECT NR_BUILTIN_CHANGE, LINE_WITH_BUILTIN FROM CommitHistoryDiffEntry WHERE COMMIT_HASH=?";
				PreparedStatement s = BuiltinAnalyzer.connection.prepareStatement(query);
				s.setString(1, selectedCommitHash);
				ResultSet rs = s.executeQuery();
				List<String[]> rows = new ArrayList<>();
				while (rs.next()) {
					String change = rs.getString(1);
					if (change.equals("1")) {
						change = "+";
					} else {
						change = "-";
					}
					String[] row = new String[] { change, rs.getString(2) };
					rows.add(row);
				}
				String[][] tableContent = rows.toArray(new String[0][0]);
				builtinTable.setModel(new TableModel() {

					@Override
					public void setValueAt(Object aValue, int rowIndex, int columnIndex) {
					}

					@Override
					public void removeTableModelListener(TableModelListener l) {
					}

					@Override
					public boolean isCellEditable(int rowIndex, int columnIndex) {
						return false;
					}

					@Override
					public Object getValueAt(int rowIndex, int columnIndex) {
						return tableContent[rowIndex][columnIndex];
					}

					@Override
					public int getRowCount() {
						return tableContent.length;
					}

					@Override
					public String getColumnName(int columnIndex) {
						String[] columnNames = new String[] { "changed", "lines" };
						return columnNames[columnIndex];
					}

					@Override
					public int getColumnCount() {
						return 2;
					}

					@Override
					public Class<?> getColumnClass(int columnIndex) {
						return String.class;
					}

					@Override
					public void addTableModelListener(TableModelListener l) {
						// TODO Auto-generated method stub

					}
				});
			} catch (Exception e) {
				throw new AssertionError(e);
			}
			builtinTable.repaint();
		}
	}

	private static void updateCommitTable() {
		if (selectedProject != null) {
			try {
				String query = "SELECT GITHUB_PROJECT_NAME, COMMIT_MESSAGE, CUR_NUMBER_BUILTINS, COMMIT_NR, COMMIT_DATE, COMMIT_HASH FROM CommitHistoryAccumulated WHERE CUR_NUMBER_BUILTINS IS NOT NULL AND GITHUB_PROJECT_ID=? ORDER BY CUR_NUMBER_BUILTINS DESC";
				PreparedStatement s = BuiltinAnalyzer.connection.prepareStatement(query);
				s.setInt(1, selectedProject.id);
				ResultSet rs = s.executeQuery();
				List<String[]> rows = new ArrayList<>();
				while (rs.next()) {
					String[] row = new String[] { rs.getString(3), rs.getString(2), rs.getString(5), rs.getString(4),
							rs.getString(6) };
					rows.add(row);
				}
				String[][] tableContent = rows.toArray(new String[0][0]);
				commitTable.setModel(new TableModel() {

					@Override
					public void setValueAt(Object aValue, int rowIndex, int columnIndex) {
					}

					@Override
					public void removeTableModelListener(TableModelListener l) {
					}

					@Override
					public boolean isCellEditable(int rowIndex, int columnIndex) {
						return false;
					}

					@Override
					public Object getValueAt(int rowIndex, int columnIndex) {
						if (rowIndex >= 0 && columnIndex >= 0) {
							return tableContent[rowIndex][columnIndex];
						} else {
							return "";
						}
					}

					@Override
					public int getRowCount() {
						return tableContent.length;
					}

					@Override
					public String getColumnName(int columnIndex) {
						String[] columnNames = new String[] { "builtin change", "commit message", "commit date",
								"commit nr", "commit hash" };
						return columnNames[columnIndex];
					}

					@Override
					public int getColumnCount() {
						return 5;
					}

					@Override
					public Class<?> getColumnClass(int columnIndex) {
						return String.class;
					}

					@Override
					public void addTableModelListener(TableModelListener l) {
						// TODO Auto-generated method stub

					}
				});
			} catch (Exception e) {
				throw new AssertionError(e);
			}
			commitTable.repaint();
		}
	}

	private static String projectFilter = "";

	private static JComboBox<String> getProjectScopeComboBox() {
		JComboBox<String> comboBox = new JComboBox<>(new String[] { "subset", "all" });
		comboBox.addItemListener(new ItemListener() {

			@Override
			public void itemStateChanged(ItemEvent e) {
				if (e.getStateChange() == ItemEvent.SELECTED) {
					String filterString = (String) e.getItem();
					switch (filterString) {
					case "subset":
						projectFilter = " AND ID IN (SELECT ID FROM RandomlySelectedProjectsForBuiltinTrends)";
						break;
					case "all":
						projectFilter = "";
						break;
					default:
						throw new AssertionError(filterString);
					}
					updateProjectList();
				}
			}

		});
		comboBox.setSelectedItem(null);
		comboBox.setSelectedItem(comboBox.getItemAt(0));
		return comboBox;
	}

	private static JComboBox<String> getFilterComboBox() throws SQLException {
		Statement s = BuiltinAnalyzer.connection.createStatement();
		List<String> filterStrings = new ArrayList<>();
		filterStrings.add("");
		ResultSet rs = s.executeQuery("SELECT TREND FROM BuiltinTrendInGithubProjectUnfiltered GROUP BY TREND");
		while (rs.next()) {
			filterStrings.add(rs.getString(1));
		}
		String[] strings = filterStrings.toArray(new String[0]);
		JComboBox<String> comboBox = new JComboBox<>(strings);
		comboBox.addItemListener(new ItemListener() {

			@Override
			public void itemStateChanged(ItemEvent e) {
				if (e.getStateChange() == ItemEvent.SELECTED) {
					filterString = (String) e.getItem();
					updateProjectList();
				}
			}

		});
		return comboBox;
	}

	private static void updateProjectList() {
		try {
			projectList.setListData(getProjectList().toArray(new GitHubProject[0]));
			projectList.repaint();
		} catch (Exception e) {
			throw new AssertionError(e);
		}
	}

	private static JComponent getProjectListPanel() throws SQLException {
		JScrollPane scrollPane = new JScrollPane();
		projectList = new JList<GitHubProject>();
		updateProjectList();
		projectList.addListSelectionListener(new ListSelectionListener() {

			@Override
			public void valueChanged(ListSelectionEvent e) {
				selectedProject = projectList.getSelectedValue();
				if (selectedProject != null) {
					imagePanel.setImage(selectedProject.getImageFile());
					updateCommitTable();
					selectedCommitHash = "";
				}
			}
		});
		scrollPane.setViewportView(projectList);
		return scrollPane;
	}

}
