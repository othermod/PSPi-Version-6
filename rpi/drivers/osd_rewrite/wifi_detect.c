// can make a separate program for each section of the osd, since some are opdated less often than others
#include <stdio.h>
#include <stdbool.h> // for boolean data types
#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include <linux/rtnetlink.h>
#include <sys/socket.h>

#define INTERFACE_NAME "wlan0"

int main() {
    int ifindex = if_nametoindex(INTERFACE_NAME);
    if (ifindex == 0) {
        perror("Error getting interface index");
        return 1;
    }

    struct {
        struct nlmsghdr nlh;
        struct ifinfomsg ifi;
    } req;

    char buf[4096];
    int fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (fd == -1) {
        perror("Error creating socket");
        return 1;
    }

    memset(&req, 0, sizeof(req));
    req.nlh.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg));
    req.nlh.nlmsg_flags = NLM_F_REQUEST;
    req.nlh.nlmsg_type = RTM_GETLINK;
    req.ifi.ifi_family = AF_UNSPEC;
    req.ifi.ifi_index = ifindex;

    while (1) { // Infinite loop
        bool isEnabled = false;
        bool isConnected = false;

        send(fd, &req, req.nlh.nlmsg_len, 0);
        int len = recv(fd, buf, sizeof(buf), 0);
        struct nlmsghdr *nh = (struct nlmsghdr *)buf;

        if (nh->nlmsg_type == RTM_NEWLINK) {
            struct ifinfomsg *ifi = NLMSG_DATA(nh);
            isEnabled = ifi->ifi_flags & IFF_UP;
            isConnected = ifi->ifi_flags & IFF_RUNNING;
        }

        printf("%s is %s\n", INTERFACE_NAME, isEnabled ? "enabled" : "disabled");
        printf("%s is %s\n", INTERFACE_NAME, isConnected ? "connected" : "disconnected");

        sleep(1); // Wait for 1 second
    }

    close(fd);

    return 0;
}
