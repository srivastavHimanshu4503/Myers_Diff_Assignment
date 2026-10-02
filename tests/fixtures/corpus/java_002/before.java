public class Logger {
    private String level;
    
    public Logger(String level) {
        this.level = level;
    }
    
    public void log(String message) {
        System.out.println("[" + level + "] " + message);
    }
}
