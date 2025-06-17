import javax.swing.*;
import java.awt.*;
import java.io.*;
import java.net.*;
import java.util.*;

public class Melon {

    // Version to download
    private static final String MC_VERSION = "1.20.1";
    private static final String MC_JAR = "minecraft.jar";
    private static final String VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json";
    private static final Map<String, Boolean> bundledMods = new LinkedHashMap<>() {{
        put("Sodium", true);
        put("Lithium", true);
        put("FerriteCore", false);
        put("DynamicFPS", false);
    }};
    private static final java.util.List<File> importedMods = new ArrayList<>();

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            setSystemLookAndFeel();
            if (!new File(MC_JAR).exists()) {
                showDownloader();
            } else {
                showLauncher();
            }
        });
    }

    private static void setSystemLookAndFeel() {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {}
    }

    // === Downloader Window ===
    private static void showDownloader() {
        JFrame frame = new JFrame("Melon 🍉 – Downloading minecraft.jar");
        frame.setSize(600, 400);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setResizable(false);
        frame.setLocationRelativeTo(null);

        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(new Color(30, 30, 30));

        JLabel status = new JLabel("<html><span style='color:white'>minecraft.jar not found.<br>Downloading Minecraft " + MC_VERSION + " from Mojang...</span></html>");
        status.setAlignmentX(Component.CENTER_ALIGNMENT);

        JProgressBar bar = new JProgressBar(0, 100);
        bar.setValue(0);
        bar.setStringPainted(true);

        panel.add(Box.createRigidArea(new Dimension(0, 16)));
        panel.add(status);
        panel.add(Box.createRigidArea(new Dimension(0, 8)));
        panel.add(bar);

        frame.setContentPane(panel);
        frame.setVisible(true);

        // Download in background thread
        new Thread(() -> {
            try {
                JSONObject manifest = readJsonUrl(VERSION_MANIFEST_URL);

                String versionUrl = null;
                JSONArray versions = manifest.getJSONArray("versions");
                for (int i = 0; i < versions.length(); i++) {
                    JSONObject v = versions.getJSONObject(i);
                    if (v.getString("id").equals(MC_VERSION)) {
                        versionUrl = v.getString("url");
                        break;
                    }
                }
                if (versionUrl == null) throw new Exception("Version not found: " + MC_VERSION);

                JSONObject versionJson = readJsonUrl(versionUrl);

                String jarUrl = versionJson.getJSONObject("downloads")
                        .getJSONObject("client")
                        .getString("url");

                status.setText("<html><span style='color:white'>Downloading minecraft.jar (" + MC_VERSION + ")<br><span style='font-size:11px'>" + jarUrl + "</span></span></html>");
                downloadFileWithBar(jarUrl, MC_JAR, bar);

                status.setText("<html><span style='color:green'>Download complete! Launching...</span></html>");
                Thread.sleep(1200);
                frame.dispose();
                showLauncher();
            } catch (Exception e) {
                status.setText("<html><span style='color:red'>Download failed: " + e.getMessage() + "</span></html>");
                bar.setForeground(Color.RED);
            }
        }).start();
    }

    // === Launcher Window ===
    private static void showLauncher() {
        JFrame frame = new JFrame("Melon 🍉 – FPS Boost Edition");
        frame.setSize(600, 400);
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

    // === PLAY PANEL ===
    private static JPanel buildPlayPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(new Color(30, 30, 30));

        JLabel userLabel = new JLabel("Username:");
        userLabel.setForeground(Color.WHITE);
        userLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        JTextField userField = new JTextField();
        userField.setMaximumSize(new Dimension(200, 30));
        userField.setAlignmentX(Component.CENTER_ALIGNMENT);

        JCheckBox offlineMode = new JCheckBox("Offline Mode");
        offlineMode.setSelected(true);
        offlineMode.setForeground(Color.LIGHT_GRAY);
        offlineMode.setBackground(new Color(30, 30, 30));
        offlineMode.setAlignmentX(Component.CENTER_ALIGNMENT);

        JButton launchBtn = new JButton("🚀 Launch Minecraft");
        launchBtn.setAlignmentX(Component.CENTER_ALIGNMENT);

        JLabel statusLabel = new JLabel(" ");
        statusLabel.setForeground(Color.GREEN);
        statusLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        launchBtn.addActionListener(e -> {
            String username = userField.getText().trim();
            boolean offline = offlineMode.isSelected();

            if (username.isEmpty()) {
                statusLabel.setText("Enter a username!");
                return;
            }

            if (offline) {
                UUID offlineUUID = UUID.nameUUIDFromBytes(("OfflinePlayer:" + username).getBytes());
                statusLabel.setText("Launching OFFLINE as " + username + " (UUID: " + offlineUUID + ")");

                try {
                    String sep = System.getProperty("os.name").toLowerCase().contains("win") ? ";" : ":";
                    File libsDir = new File("libs");
                    StringBuilder classpath = new StringBuilder(MC_JAR);

                    if (libsDir.exists() && libsDir.isDirectory()) {
                        File[] jars = libsDir.listFiles((d, name) -> name.endsWith(".jar"));
                        if (jars != null) {
                            for (File jar : jars) {
                                classpath.append(sep).append("libs/").append(jar.getName());
                            }
                        }
                    }

                    for (File mod : importedMods) {
                        if (!classpath.toString().contains(mod.getAbsolutePath())) {
                            classpath.append(sep).append(mod.getAbsolutePath());
                        }
                    }

                    java.util.List<String> command = new ArrayList<>();
                    command.add("java");
                    command.add("-Xmx2G");
                    command.add("-Djava.library.path=natives");
                    command.add("-cp");
                    command.add(classpath.toString());
                    command.add("net.minecraft.client.main.Main");
                    command.add("--username");
                    command.add(username);

                    new ProcessBuilder(command)
                            .inheritIO()
                            .start();

                } catch (IOException ex) {
                    statusLabel.setText("Error launching game: " + ex.getMessage());
                    ex.printStackTrace();
                }
            } else {
                statusLabel.setForeground(Color.ORANGE);
                statusLabel.setText("Online mode not implemented. Only offline mode is supported in this build.");
            }
        });

        panel.add(Box.createVerticalGlue());
        panel.add(userLabel);
        panel.add(userField);
        panel.add(Box.createRigidArea(new Dimension(0, 10)));
        panel.add(offlineMode);
        panel.add(Box.createRigidArea(new Dimension(0, 10)));
        panel.add(launchBtn);
        panel.add(statusLabel);
        panel.add(Box.createVerticalGlue());
        return panel;
    }

    // === MODS PANEL ===
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

        JLabel importedLabel = new JLabel("Imported Mods:");
        importedLabel.setForeground(Color.LIGHT_GRAY);
        modListPanel.add(Box.createRigidArea(new Dimension(0, 10)));
        modListPanel.add(importedLabel);

        DefaultListModel<String> importedListModel = new DefaultListModel<>();
        JList<String> importedList = new JList<>(importedListModel);
        importedList.setBackground(new Color(35, 35, 35));
        importedList.setForeground(Color.WHITE);

        JButton importButton = new JButton("➕ Import Mod");
        importButton.addActionListener(e -> {
            JFileChooser chooser = new JFileChooser();
            chooser.setFileSelectionMode(JFileChooser.FILES_ONLY);
            if (chooser.showOpenDialog(panel) == JFileChooser.APPROVE_OPTION) {
                File selected = chooser.getSelectedFile();
                if (selected.getName().endsWith(".jar")) {
                    importedMods.add(selected);
                    importedListModel.addElement(selected.getName());
                    JOptionPane.showMessageDialog(panel, "Imported: " + selected.getName());
                } else {
                    JOptionPane.showMessageDialog(panel, "Invalid file type. Please select a .jar file.", "Error", JOptionPane.ERROR_MESSAGE);
                }
            }
        });

        JScrollPane importedScroll = new JScrollPane(importedList);
        importedScroll.setPreferredSize(new Dimension(200, 80));
        modListPanel.add(importedScroll);

        panel.add(new JScrollPane(modListPanel), BorderLayout.CENTER);
        panel.add(importButton, BorderLayout.SOUTH);
        return panel;
    }

    // === UTILS ===
    private static JSONObject readJsonUrl(String url) throws Exception {
        URL u = new URL(url);
        try (InputStream in = u.openStream()) {
            String text = new String(in.readAllBytes(), "UTF-8");
            return new JSONObject(text);
        }
    }

    private static void downloadFileWithBar(String url, String outFile, JProgressBar bar) throws Exception {
        URL u = new URL(url);
        HttpURLConnection conn = (HttpURLConnection) u.openConnection();
        int size = conn.getContentLength();

        try (InputStream in = conn.getInputStream();
             FileOutputStream out = new FileOutputStream(outFile)) {
            byte[] buffer = new byte[8192];
            int read;
            int total = 0;
            while ((read = in.read(buffer)) > 0) {
                out.write(buffer, 0, read);
                total += read;
                int percent = (size > 0) ? (int)(100L * total / size) : 0;
                bar.setValue(percent);
            }
        }
    }
}

// --- Minimal JSON classes, built-in ---
// Only what's needed for parsing Minecraft's manifest.

class JSONObject extends HashMap<String, Object> {
    public JSONObject(String src) { this(new JSONTokener(src)); }
    public JSONObject(JSONTokener tok) {
        char c;
        String key;
        if (tok.nextClean() != '{') throw tok.syntax("A JSONObject text must begin with '{'");
        for (;;) {
            c = tok.nextClean();
            if (c == 0) throw tok.syntax("A JSONObject text must end with '}'");
            if (c == '}') break;
            tok.back();
            key = tok.nextValue().toString();
            if (tok.nextClean() != ':') throw tok.syntax("Expected a ':' after a key");
            Object value = tok.nextValue();
            put(key, value);
            switch (tok.nextClean()) {
                case ';': case ',':
                    if (tok.nextClean() == '}') return;
                    tok.back();
                    break;
                case '}': return;
                default: throw tok.syntax("Expected a ',' or '}'");
            }
        }
    }
    public JSONArray getJSONArray(String key) { return (JSONArray) get(key); }
    public JSONObject getJSONObject(String key) { return (JSONObject) get(key); }
    public String getString(String key) { return get(key).toString(); }
    public int getInt(String key) { return ((Number) get(key)).intValue(); }
}

class JSONArray extends ArrayList<Object> {
    public JSONArray(String src) { this(new JSONTokener(src)); }
    public JSONArray(JSONTokener tok) {
        if (tok.nextClean() != '[') throw tok.syntax("A JSONArray text must start with '['");
        if (tok.nextClean() == ']') return;
        tok.back();
        for (;;) {
            if (tok.nextClean() == ',') { tok.back(); add(null); }
            else { tok.back(); add(tok.nextValue()); }
            switch (tok.nextClean()) {
                case ',':
                    if (tok.nextClean() == ']') return;
                    tok.back();
                    break;
                case ']': return;
                default: throw tok.syntax("Expected a ',' or ']'");
            }
        }
    }
    public JSONObject getJSONObject(int idx) { return (JSONObject) get(idx); }
    public String getString(int idx) { return get(idx).toString(); }
    public int length() { return size(); }
}

class JSONTokener {
    private final String src;
    private int pos = 0;
    public JSONTokener(String src) { this.src = src.trim(); }
    public char next() { return pos < src.length() ? src.charAt(pos++) : 0; }
    public void back() { if (pos > 0) pos--; }
    public char nextClean() {
        char c;
        do c = next(); while (c != 0 && c <= ' ');
        return c;
    }
    public Object nextValue() {
        char c = nextClean();
        switch (c) {
            case '"': case '\'': return nextString(c);
            case '{': back(); return new JSONObject(this);
            case '[': back(); return new JSONArray(this);
            default:
                StringBuilder sb = new StringBuilder();
                while (c >= ' ' && ",:]}/\\\"[{;=#".indexOf(c) < 0) {
                    sb.append(c); c = next();
                }
                back();
                String s = sb.toString().trim();
                if ("true".equals(s)) return Boolean.TRUE;
                if ("false".equals(s)) return Boolean.FALSE;
                if ("null".equals(s)) return null;
                try { return Integer.parseInt(s); } catch (Exception ignore) {}
                try { return Double.parseDouble(s); } catch (Exception ignore) {}
                return s;
        }
    }
    private String nextString(char quote) {
        StringBuilder sb = new StringBuilder();
        for (;;) {
            char c = next();
            if (c == quote) return sb.toString();
            if (c == '\\') {
                c = next();
                switch (c) {
                    case 'b': sb.append('\b'); break;
                    case 't': sb.append('\t'); break;
                    case 'n': sb.append('\n'); break;
                    case 'f': sb.append('\f'); break;
                    case 'r': sb.append('\r'); break;
                    case 'u':
                        sb.append((char) Integer.parseInt(src.substring(pos, pos+4), 16));
                        pos += 4;
                        break;
                    default: sb.append(c);
                }
            } else sb.append(c);
        }
    }
    RuntimeException syntax(String msg) { return new RuntimeException(msg + " at " + pos); }
}
