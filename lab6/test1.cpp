#include <thread>
#include <iostream>

using namespace std;

void f1(){
    cout << "f1" << endl;
}

void f2(int arg){
    cout << "f2:" << arg << endl;
}

int main(){
    thread t1;
    thread t2(f1);
    thread t3(f2,10);

    t2.join();
    t3.join();

    return 0;
}