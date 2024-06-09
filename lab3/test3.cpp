#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <string.h>
#include <unistd.h>


#include <iostream>
#include <string>


using namespace std;


int main() {
    int s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (s < 0) return 1;

    string buf = "Hello Wolrd";

    struct sockaddr_in sin;
    memset(&sin,0,sizeof(sin)); // sin의 사이즈 만큼 0으로 채워라
    sin.sin_family = AF_INET; // IPv4 명시
    sin.sin_port = htons(10000); // 바이트 맞추기 Big-Endian으로 바꿔줌
    sin.sin_addr.s_addr = inet_addr("127.0.0.1"); 

    int numBytes = sendto(s, buf.c_str(), buf.length(),0, (struct sockaddr *) &sin, sizeof(sin));
    cout << "Sent: " << numBytes << endl;
    // 11글자 보냈다고 나오지만, 해당 네트워크로 전달된지는 모른다. UDP는 네트워크에 보내긴했다는 뜻이다.

    close(s);
    return 0;
}
