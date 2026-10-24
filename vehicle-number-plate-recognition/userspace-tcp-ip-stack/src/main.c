#include "packet.h"

#include <stdio.h>

int main(void) {
    uint8_t buffer[256];
    ipv4_header_t ip;
    tcp_header_t tcp;
    size_t total;
    const char *payload = "hello";

    total = packet_build_ipv4_tcp(buffer, sizeof(buffer), 0x0a000001u, 0x0a000002u,
                                  12345, 80, (const uint8_t *)payload, 5);
    printf("built %zu bytes\n", total);
    if (packet_parse_ipv4(buffer, total, &ip) == 0) {
        fprintf(stderr, "bad ip header\n");
        return 1;
    }
    if (packet_parse_tcp(buffer + IPV4_HEADER, total - IPV4_HEADER, &tcp) == 0) {
        fprintf(stderr, "bad tcp header\n");
        return 1;
    }
    printf("ip ttl=%u protocol=%u checksum=0x%04x\n", ip.ttl, ip.protocol, ip.checksum);
    printf("tcp %u -> %u flags=0x%02x\n", tcp.source_port, tcp.destination_port, tcp.flags);
    printf("ipv4 checksum valid: %s\n", packet_checksum(buffer, IPV4_HEADER) == 0 ? "yes" : "no");
    return 0;
}
