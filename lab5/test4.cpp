#include <arpa/inet.h>
#include <errno.h>
#include <string.h>
#include <sys/socket.h>

#include <unistd.h>
#include <iostream>

using namespace std;

int main(){
    int s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
     if(s < 0) {
            cerr << "socket() failed: " << " " << strerror(errno) << endl;
            return 1;
        }
    close(s);
    char buf[1024];
    int r = send(s, buf, sizeof(buf), MSG_NOSIGNAL); // OS가 시그널 보내서 죽이는걸 방지
    if (r < 0){
        cerr << "send() failed: " << strerror(errno) << endl;
    } else {
        cout << "Sent: " << r << "bytes" << endl;
    }
    close(s);
    return 0;
}