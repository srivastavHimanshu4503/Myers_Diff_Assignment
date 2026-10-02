public class Logger {
    private String level;
    private boolean enabled;
    
    public Logger(String level) {
        this.level = level;
        this.enabled = true;
    }
    
    public void log(String message) {
        if (enabled) {
            System.out.println("[" + level + "] " + message);
        }
    }
}
