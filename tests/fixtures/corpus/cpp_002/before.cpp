namespace Utils {
    template<typename T>
    class Container {
    private:
        T* data;
        size_t size;
    public:
        Container() : data(nullptr), size(0) {}
        ~Container() { delete[] data; }
    };
}
