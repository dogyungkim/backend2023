#include <atomic>
#include <chrono>
#include <iostream>
#include <thread>

using namespace std;

atomic<bool> quit = false;

void f(){
    for (int i = 0; quit.load() == false && i < 5; ++i){
        cout << "Running: " << this_thread::get_id() << endl;
        this_thread::sleep_for(chrono::milliseconds(1000));
    }
}

int main(){
    thread t1(f);
    this_thread::sleep_for(chrono::microseconds(2500));
    quit.store(true);
    t1.join();
    return 1;
}
