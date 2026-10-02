namespace Utils {
    template<typename T>
    class Container {
    private:
        T* data;
        size_t size;
        size_t capacity;
    public:
        Container() : data(nullptr), size(0), capacity(0) {}
        ~Container() { delete[] data; }
    };
}
