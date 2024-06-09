#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <string.h>
#include <unistd.h>


#include <iostream>
#include <string>


using namespace std;

int main(){

    //소켓생성
    int s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (s < 0) return 1;

    //필요 변수들
    struct sockaddr_in sin;
    socklen_t sin_size; //소켓 사이즈


    char buf[65536]; //메시지 버퍼
    int numBytes; //받은 메시지 크기
    

    //소켓 설정
    memset(&sin, 0, sizeof(sin));
    sin.sin_family = AF_INET;
    sin.sin_addr.s_addr = INADDR_ANY;
    sin.sin_port = htons(20000 + 106);


    //Bind
    if (bind(s, (struct sockaddr *) &sin, sizeof(sin)) < 0) {
        cerr << strerror(errno) << endl;
        return 0;
    }

    

    //서버 가동 
    while(1){
        cout << "----------------" << endl;
        cout << "Server Ready" << endl;
        sin_size = sizeof(sin);

        numBytes = recvfrom(s, buf, sizeof(buf), 0, (struct sockaddr *) &sin, &sin_size);
        if (numBytes < 0) { cout << "recvError " << endl; }

        cout << "From: " << inet_ntoa(sin.sin_addr) << endl;
        cout << "Recieved: " << numBytes << endl;
        cout << "Msg: " << buf << endl;

        numBytes = sendto(s, buf, numBytes, 0, (struct sockaddr *) &sin, sizeof(sin));

        cout << "Sent: " << numBytes << endl << endl;
        
        memset(&sin,0,sizeof(sin)); //sin을 활용하기전에 초기화
    }

    close(s);
    return 0;
}