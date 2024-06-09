#include <condition_variable>
#include <iostream>
#include <mutex>
#include <thread>

using namespace std;

mutex m;
condition_variable cv;

int sum = 0;

void f(){
    for (int i = 0; i < 10 * 1000 * 1000; ++i){
        ++sum;  
    }
    {
        cout << "locked" << endl;
        unique_lock<mutex> lg(m);
        cout << "notify" << endl;
        cv.notify_one();
    }
}

int main(){
    thread t(f);
    {
        cout << "main locked" << endl;
        unique_lock<mutex> lg(m);
        cout << "wait" << endl;
        cv.wait(lg);
        
        cout << "Sum: " << sum << endl;
    }
    t.join();
}