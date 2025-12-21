public class Greeter {
    private String name;
    
    public Greeter(String name) {
        this.name = name;
    }
    
    public String greet() {
        return "Hello, " + name + "!";
    }
    
    public static void main(String[] args) {
        Greeter greeter = new Greeter("World");
        System.out.println(greeter.greet());
    }
}

