#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "../src/packet.h"

static void test_the_checksum(void) {
    uint8_t header[20];
    memset(header, 0, sizeof(header));
    header[0] = 0x45;
    header[3] = 20;

    uint16_t checksum = packet_checksum(header, sizeof(header));
    // The checksum of a header that has the checksum in it is zero.
    header[10] = (uint8_t)(checksum >> 8);
    header[11] = (uint8_t)(checksum & 0xff);
    assert(packet_checksum(header, sizeof(header)) == 0);
}

static void test_read_and_write(void) {
    uint8_t buffer[4] = {0x12, 0x34, 0x56, 0x78};
    assert(packet_read_u16(buffer) == 0x1234);
    assert(packet_read_u32(buffer) == 0x12345678u);

    uint8_t out[4];
    packet_write_u16(out, 0xabcd);
    assert(out[0] == 0xab && out[1] == 0xcd);
    packet_write_u32(out, 0x01020304u);
    assert(out[0] == 1 && out[3] == 4);
}

static void test_the_ipv4_header_is_parsed(void) {
    uint8_t packet[20];
    memset(packet, 0, sizeof(packet));
    packet[0] = 0x45;
    packet[9] = 6;

    ipv4_header_t header;
    // The length of the header is returned, and zero when the packet is
    // broken.
    assert(packet_parse_ipv4(packet, sizeof(packet), &header) == IPV4_HEADER);
    assert((header.version_ihl >> 4) == 4);
    assert(header.protocol == 6);
}

static void test_the_tcp_header_is_parsed(void) {
    uint8_t packet[20];
    memset(packet, 0, sizeof(packet));
    packet[0] = 0x50;
    packet_write_u16(packet, 1234);
    packet_write_u16(packet + 2, 443);

    tcp_header_t header;
    assert(packet_parse_tcp(packet, sizeof(packet), &header) == TCP_HEADER);
    assert(header.source_port == 1234);
    assert(header.destination_port == 443);
}

static void test_a_short_buffer_is_refused(void) {
    uint8_t packet[4] = {0x45, 0, 0, 0};
    ipv4_header_t header;
    // A packet that is too short is refused.
    assert(packet_parse_ipv4(packet, sizeof(packet), &header) == 0);
}

static void test_a_packet_is_built(void) {
    uint8_t buffer[64];
    uint8_t payload[4] = {1, 2, 3, 4};

    size_t length = packet_build_ipv4_tcp(buffer, sizeof(buffer), 0x0a000001, 0x0a000002,
                                        1234, 80, payload, sizeof(payload));
    assert(length >= IPV4_HEADER + TCP_HEADER + sizeof(payload));

    ipv4_header_t ip;
    assert(packet_parse_ipv4(buffer, length, &ip) == IPV4_HEADER);
    assert(ip.protocol == 6);
}

int main(void) {
    test_the_checksum();
    test_read_and_write();
    test_the_ipv4_header_is_parsed();
    test_the_tcp_header_is_parsed();
    test_a_short_buffer_is_refused();
    test_a_packet_is_built();
    printf("all packet tests passed\n");
    return 0;
}
