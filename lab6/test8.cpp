#include <chrono>
#include <iostream>
#include <mutex>
#include <thread>

using namespace std;

mutex m;

int sum = 0;

void f(){
    for (int i = 0; i < 10 * 1000 * 1000; ++i){
        {
            unique_lock<mutex> ul(m);
            ++sum;  
        }
    }
}

int main(){
    thread t(f);
    for (int i = 0; i < 10 * 1000 * 1000; ++i){
        {
            unique_lock<mutex> ul(m);
            ++sum;  
        } 
    }
    t.join();
    cout << "Sum: " << sum << endl;
}