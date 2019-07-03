import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;
import javax.swing.event.TableModelListener;
import javax.swing.table.DefaultTableCellRenderer;
import javax.swing.table.TableModel;

public class ConsensusFindingGUI {

	private static JList<GitHubProject> projectList;
	private static GitHubProject selectedProject;
	static ImagePanel imagePanel = new ImagePanel();
	static JTable classificationTable = new JTable();
	static List<String[]> classifications = new ArrayList<>();
	private static String filterString = "WHERE 1=1";

	public static void main(String[] args) throws Exception {
		JFrame frame = new JFrame("");
		JComponent projectList = getProjectListPanel();
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		JPanel leftPanel = new JPanel();
		leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
		JComboBox<String> comboBox = getFilterComboBox();
		comboBox.setMaximumSize(new Dimension(comboBox.getMaximumSize().width, 10));
		leftPanel.add(comboBox);
		JComboBox<String> comboBox2 = getTrendFilterComboBox();
		comboBox2.setMaximumSize(new Dimension(comboBox2.getMaximumSize().width, 10));
		leftPanel.add(comboBox2);
		JComboBox<String> comboBox3 = getNrTrendsCombobox();
		comboBox3.setMaximumSize(new Dimension(comboBox3.getMaximumSize().width, 10));
		leftPanel.add(comboBox3);
		leftPanel.add(projectList);
		frame.getContentPane().add(leftPanel, BorderLayout.WEST);

		ActionListener buttonListener = new ActionListener() {

			@Override
			public void actionPerformed(ActionEvent e) {
				try {
					for (GitHubProject project : ConsensusFindingGUI.projectList.getSelectedValuesList()) {
						PreparedStatement newClassification = BuiltinAnalyzer.connection.prepareStatement(
								"INSERT OR REPLACE INTO BuiltinTrendInGithubProjectUnfiltered(GITHUB_PROJECT_ID, TREND, USER) VALUES(?, ?, ?)");
						newClassification.setInt(1, project.id);
						newClassification.setString(2, ((JButton) e.getSource()).getText());
						newClassification.setString(3, "resolver-2");
						newClassification.executeUpdate();
						newClassification.close();
						BuiltinAnalyzer.connection.commit();
					}
					updateProjectList();
				} catch (Exception exc) {
					throw new AssertionError(exc);
				}
			}
		};

		JPanel buttonPanel = new JPanel();
		buttonPanel.setLayout(new BoxLayout(buttonPanel, BoxLayout.Y_AXIS));
		addButton(buttonPanel, buttonListener, "increasing, then decreasing");
//		addButton(scrollPane, buttonListener, "decreasing, then increasing");
//		addButton(scrollPane, buttonListener, "decreasing, then stable");
		addButton(buttonPanel, buttonListener, "mostly increasing");
//		addButton(scrollPane, buttonListener, "mostly decreasing");
//		addButton(scrollPane, buttonListener, "decreasing, then stable");
		addButton(buttonPanel, buttonListener, "increasing, then stable");
		addButton(buttonPanel, buttonListener, "mostly stable");
		addButton(buttonPanel, buttonListener, "spike, then stable"); // up and down
		addButton(buttonPanel, buttonListener, "stable, then increasing");
//		addButton(scrollPane, buttonListener, "stable, then decreasing");
		addButton(buttonPanel, buttonListener, "no clear pattern");
		addButton(buttonPanel, buttonListener, "not yet decided");
		addButton(buttonPanel, buttonListener, "initial import");

		JPanel mainPanel = new JPanel();
		mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
		mainPanel.add(imagePanel);
		mainPanel.add(buttonPanel);
		JPanel rightPanel = new JPanel();
		rightPanel.setLayout(new BoxLayout(rightPanel, BoxLayout.Y_AXIS));
		rightPanel.add(classificationTable);
		frame.getContentPane().add(mainPanel, BorderLayout.CENTER);
		mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
		frame.getContentPane().add(rightPanel, BorderLayout.NORTH);
		frame.pack();
		Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
		frame.setSize(d);
		frame.setVisible(true);
		classificationTable.setFont(new Font("Verdana", Font.PLAIN, 20));
		classificationTable.setMaximumSize(new Dimension(600, 300));

		classificationTable.setDefaultRenderer(String.class, new DefaultTableCellRenderer() {

			private static final long serialVersionUID = 1L;

			private final Map<String, Color> colorMap = new HashMap<>();
			private final List<Color> colors = new ArrayList<>(Arrays.asList(Color.decode("0xFF7373"),
					Color.decode("0xE37795"), Color.decode("0xD900D9"), Color.decode("0xBA21E0"),
					Color.decode("0x8282FF"), Color.decode("0x4FBDDD"), Color.decode("0x8DC7BB"),
					Color.decode("0xDBDB97"), Color.decode("0xD29680"), Color.decode("0xDD75DD")));

			{
				Statement statement = BuiltinAnalyzer.connection.createStatement();
				ResultSet rs = statement.executeQuery(
						"SELECT DISTINCT TREND FROM BuiltinTrendInGithubProjectUnfiltered ORDER BY TREND");
				while (rs.next()) {
					colorMap.put(rs.getString(1), colors.remove(0));
				}
			}

			@Override
			public Component getTableCellRendererComponent(JTable table, Object value, boolean isSelected,
					boolean hasFocus, int row, int column) {
				super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column);
				setBackground(colorMap.get(table.getValueAt(row, 1)));
				return this;
			}
		});
		classificationTable.setModel(new TableModel() {

			String[] columns = { "classifier", "classification" };

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
				return classifications.get(rowIndex)[columnIndex];
			}

			@Override
			public int getRowCount() {
				return classifications.size();
			}

			@Override
			public String getColumnName(int columnIndex) {
				return columns[columnIndex];
			}

			@Override
			public int getColumnCount() {
				return columns.length;
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
	}

	static void addButton(JComponent buttonPanel, ActionListener buttonListener, String text) {
		JButton mostlyIncreasing = new JButton(text);
		mostlyIncreasing.addActionListener(buttonListener);
		buttonPanel.add(mostlyIncreasing);
	}

	private static String trendFilterString = "";
	
	private static JComboBox<String> getTrendFilterComboBox() throws SQLException {
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
					trendFilterString = (String) e.getItem();
					updateProjectList();
				}
			}

		});
		return comboBox;
	}


	public static List<GitHubProject> getProjectList() throws SQLException {
		List<GitHubProject> projectList = new ArrayList<GitHubProject>();
		String sql = "SELECT t1.*, GROUP_CONCAT(TREND, \";\") as trends FROM ResolvedBuiltinTrends t1 JOIN BuiltinTrendInGithubProjectUnfiltered t2 ON t1.GITHUB_PROJECT_ID = t2.GITHUB_PROJECT_ID ";
		sql += filterString;
		if (!trendFilterString.isEmpty()) {
			sql +=  " AND TREND='" + trendFilterString + "'";
		}
		if (!nrTrendsFilter.isEmpty()) {
			sql += " " + nrTrendsFilter;
		}
		sql += " GROUP BY t1.GITHUB_PROJECT_ID";
		Statement s = BuiltinAnalyzer.connection.createStatement();
		ResultSet rs = s.executeQuery(sql);
		GitHubProject.addRsAsGithubProjects(projectList, rs);
		return projectList;
	}

	private static JComboBox<String> getFilterComboBox() throws SQLException {
		List<String> filterStrings = new ArrayList<>();
		filterStrings.add("all");
		filterStrings.add("unresolved");
		filterStrings.add("resolved");
		String[] strings = filterStrings.toArray(new String[0]);
		JComboBox<String> comboBox = new JComboBox<>(strings);
		comboBox.addItemListener(new ItemListener() {

			@Override
			public void itemStateChanged(ItemEvent e) {
				if (e.getStateChange() == ItemEvent.SELECTED) {
					String selection = (String) e.getItem();
					if (selection.equals("all")) {
						filterString = "WHERE 1=1";
					} else if (selection.equals("unresolved")) {
						filterString = "WHERE status = 'unresolved'";
					} else if (selection.equals("resolved")) {
						filterString = "WHERE (status = 'resolved' or status = 'resolver-2')";
					} else {
						throw new AssertionError(selection);
					}
					updateProjectList();
				}
			}

		});
		return comboBox;
	}
	
	private static JComboBox<String> getNrTrendsCombobox() throws SQLException {
		List<String> filterStrings = new ArrayList<>();
		Statement s = BuiltinAnalyzer.connection.createStatement();
		ResultSet rs = s.executeQuery("SELECT DISTINCT nr_trends FROM ResolvedBuiltinTrends");
		filterStrings.add("all trends");
		while (rs.next()) {
			filterStrings.add(rs.getString(1));
		}
		String[] strings = filterStrings.toArray(new String[0]);
		JComboBox<String> comboBox = new JComboBox<>(strings);
		comboBox.addItemListener(new ItemListener() {


			@Override
			public void itemStateChanged(ItemEvent e) {
				if (e.getStateChange() == ItemEvent.SELECTED) {
					String nrTrends = (String) e.getItem();
					if (nrTrends.equals("all trends")) {
						nrTrendsFilter = "";
					} else {
						nrTrendsFilter = "AND nr_trends=" + nrTrends;
					}
					updateProjectList();
				}
			}

		});
		return comboBox;
	}

	private static String nrTrendsFilter = "";

	private static void updateProjectList() {
		try {
			projectList.setListData(getProjectList().toArray(new GitHubProject[0]));
			projectList.revalidate();
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
				}
				try {
					classifications.clear();
					Statement s = BuiltinAnalyzer.connection.createStatement();
					if (selectedProject != null) {
						String sql = "SELECT USER, TREND FROM BuiltinTrendInGithubProjectUnfiltered WHERE GITHUB_PROJECT_ID="
								+ selectedProject.id;
						ResultSet rs = s.executeQuery(sql);
						while (rs.next()) {
							String user = rs.getString(1);
							String trend = rs.getString(2);
							classifications.add(new String[] { user, trend });
						}
					}
					classificationTable.revalidate();
					classificationTable.repaint();
				} catch (SQLException e1) {
					// TODO Auto-generated catch block
					e1.printStackTrace();
				}
			}
		});
		
		scrollPane.setViewportView(projectList);
		return scrollPane;
	}

}
