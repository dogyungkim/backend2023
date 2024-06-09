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

    //For packet bytes
    int sentByte;
    int recvByte;

    //for recv()
    char buf2[65536];

    //sending msg
    string buf = "";

    struct sockaddr_in sin;
    socklen_t sin_size;

    memset(&sin,0,sizeof(sin)); 
    sin.sin_family = AF_INET; 
    sin.sin_port = htons(20000 + 106);
    sin.sin_addr.s_addr = inet_addr("127.0.0.1"); 

    while(getline(cin, buf)){

        int numBytes = sendto(s, buf.c_str(), buf.length(),0, (struct sockaddr *) &sin, sizeof(sin));
        cout << "Sent: " << numBytes << endl;
        
        
        sin_size = sizeof(sin);
        
        memset(buf2,0,sizeof(char)*65536);
        numBytes = recvfrom(s, buf2, sizeof(buf2), 0,(struct sockaddr *) &sin, &sin_size);


        cout << "Recieved: " << numBytes << endl;
        cout << "Message: " << buf2 << endl;
        cout << "From: " << inet_ntoa(sin.sin_addr) << endl; // 4바이트를 문자열로 바꾸기 network to ascii

    }
    close(s);
    return 0;
}
