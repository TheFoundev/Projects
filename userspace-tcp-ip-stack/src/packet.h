#ifndef PACKET_H
#define PACKET_H

#include <stddef.h>
#include <stdint.h>

#define ETHERNET_HEADER 14
#define IPV4_HEADER 20
#define TCP_HEADER 20

typedef struct {
    uint8_t destination[6];
    uint8_t source[6];
    uint16_t ethertype;
} ethernet_header_t;

typedef struct {
    uint8_t version_ihl;
    uint8_t dscp_ecn;
    uint16_t total_length;
    uint16_t identification;
    uint16_t flags_fragment;
    uint8_t ttl;
    uint8_t protocol;
    uint16_t checksum;
    uint32_t source;
    uint32_t destination;
} ipv4_header_t;

typedef struct {
    uint16_t source_port;
    uint16_t destination_port;
    uint32_t sequence;
    uint32_t acknowledgement;
    uint8_t data_offset;
    uint8_t flags;
    uint16_t window;
    uint16_t checksum;
    uint16_t urgent;
} tcp_header_t;

uint16_t packet_checksum(const uint8_t *data, size_t length);
uint16_t packet_read_u16(const uint8_t *data);
uint32_t packet_read_u32(const uint8_t *data);
void packet_write_u16(uint8_t *data, uint16_t value);
void packet_write_u32(uint8_t *data, uint32_t value);
int packet_parse_ethernet(const uint8_t *data, size_t length, ethernet_header_t *header);
int packet_parse_ipv4(const uint8_t *data, size_t length, ipv4_header_t *header);
int packet_parse_tcp(const uint8_t *data, size_t length, tcp_header_t *header);
size_t packet_build_ipv4_tcp(uint8_t *buffer, size_t capacity, uint32_t source, uint32_t destination,
                             uint16_t source_port, uint16_t destination_port,
                             const uint8_t *payload, size_t payload_length);

#endif
