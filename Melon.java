import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.File;
import java.io.IOException;
import java.util.*;

public class MelonClientLauncher {

    private static final Map<String, Boolean> bundledMods = new LinkedHashMap<>() {{
        put("Sodium", true);
        put("Lithium", true);
        put("FerriteCore", false);
        put("DynamicFPS", false);
    }};

    private static final java.util.List<File> importedMods = new ArrayList<>();

    public static void main(String[] args) {
        JFrame frame = new JFrame("Melon Client 🍉 – FPS Boost Edition");
        frame.setSize(800, 600);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setResizable(false);
        frame.setLocationRelativeTo(null);

        JTabbedPane tabs = new JTabbedPane();
        tabs.addTab("Play", buildPlayPanel());
        tabs.addTab("Mods", buildModsPanel());
        tabs.addTab("Settings", new JPanel());
        tabs.addTab("Voice Chat", new JPanel());
        tabs.addTab("Server Host", new JPanel());
        tabs.addTab("Skins", new JPanel());

        frame.setContentPane(tabs);
        frame.setVisible(true);
    }

    private static JPanel buildPlayPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(new Color(30, 30, 30));

        JLabel userLabel = new JLabel("Username (Offline Mode):");
        userLabel.setForeground(Color.WHITE);
        userLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        JTextField userField = new JTextField();
        userField.setMaximumSize(new Dimension(200, 30));
        userField.setAlignmentX(Component.CENTER_ALIGNMENT);

        JButton launchBtn = new JButton("🚀 Launch Minecraft");
        launchBtn.setAlignmentX(Component.CENTER_ALIGNMENT);

        JLabel statusLabel = new JLabel(" ");
        statusLabel.setForeground(Color.GREEN);
        statusLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        launchBtn.addActionListener(e -> {
            String username = userField.getText().trim();
            if (username.isEmpty()) {
                statusLabel.setText("Enter a username!");
                return;
            }

            UUID offlineUUID = UUID.nameUUIDFromBytes(("OfflinePlayer:" + username).getBytes());
            statusLabel.setText("Launching as " + username + " (UUID: " + offlineUUID + ")");

            try {
                java.util.List<String> command = new java.util.ArrayList<>();
                command.add("java");
                command.add("-Xmx2G"); // RAM setting
                command.add("-Djava.library.path=natives");
                command.add("-cp");
                command.add("minecraft.jar;libs/*"); // Classpath
                command.add("net.minecraft.client.main.Main");
                command.add("--username");
                command.add(username);

                // Optionally append mods info (not passed to vanilla MC directly)

                new ProcessBuilder(command)
                        .inheritIO()
                        .start();

            } catch (IOException ex) {
                statusLabel.setText("Error launching game: " + ex.getMessage());
                ex.printStackTrace();
            }
        });

        panel.add(Box.createVerticalGlue());
        panel.add(userLabel);
        panel.add(userField);
        panel.add(Box.createRigidArea(new Dimension(0, 10)));
        panel.add(launchBtn);
        panel.add(statusLabel);
        panel.add(Box.createVerticalGlue());
        return panel;
    }

    private static JPanel buildModsPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BorderLayout());
        panel.setBackground(new Color(30, 30, 30));

        JPanel modListPanel = new JPanel();
        modListPanel.setLayout(new BoxLayout(modListPanel, BoxLayout.Y_AXIS));
        modListPanel.setBackground(new Color(30, 30, 30));

        for (String modName : bundledMods.keySet()) {
            JCheckBox checkBox = new JCheckBox(modName);
            checkBox.setSelected(bundledMods.get(modName));
            checkBox.setForeground(Color.WHITE);
            checkBox.setBackground(new Color(40, 40, 40));
            checkBox.addActionListener(e -> bundledMods.put(modName, checkBox.isSelected()));
            modListPanel.add(checkBox);
        }

        JButton importButton = new JButton("➕ Import Mod");
        importButton.addActionListener(e -> {
            JFileChooser chooser = new JFileChooser();
            chooser.setFileSelectionMode(JFileChooser.FILES_ONLY);
            if (chooser.showOpenDialog(panel) == JFileChooser.APPROVE_OPTION) {
                File selected = chooser.getSelectedFile();
                importedMods.add(selected);
                JOptionPane.showMessageDialog(panel, "Imported: " + selected.getName());
            }
        });

        panel.add(new JScrollPane(modListPanel), BorderLayout.CENTER);
        panel.add(importButton, BorderLayout.SOUTH);
        return panel;
    }
}
