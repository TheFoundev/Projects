#include "packet.h"

#include <string.h>

uint16_t packet_read_u16(const uint8_t *data) {
    return (uint16_t)((data[0] << 8) | data[1]);
}

uint32_t packet_read_u32(const uint8_t *data) {
    return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) |
           ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

void packet_write_u16(uint8_t *data, uint16_t value) {
    data[0] = (uint8_t)(value >> 8);
    data[1] = (uint8_t)(value & 0xff);
}

void packet_write_u32(uint8_t *data, uint32_t value) {
    data[0] = (uint8_t)(value >> 24);
    data[1] = (uint8_t)(value >> 16);
    data[2] = (uint8_t)(value >> 8);
    data[3] = (uint8_t)(value & 0xff);
}

uint16_t packet_checksum(const uint8_t *data, size_t length) {
    uint32_t sum = 0;
    size_t index;
    for (index = 0; index + 1 < length; index += 2) {
        sum += packet_read_u16(data + index);
    }
    if (index < length) {
        sum += (uint16_t)(data[index] << 8);
    }
    while (sum >> 16) {
        sum = (sum & 0xffff) + (sum >> 16);
    }
    return (uint16_t)(~sum);
}

int packet_parse_ethernet(const uint8_t *data, size_t length, ethernet_header_t *header) {
    if (length < ETHERNET_HEADER) {
        return 0;
    }
    memcpy(header->destination, data, 6);
    memcpy(header->source, data + 6, 6);
    header->ethertype = packet_read_u16(data + 12);
    return ETHERNET_HEADER;
}

int packet_parse_ipv4(const uint8_t *data, size_t length, ipv4_header_t *header) {
    size_t header_length;
    if (length < IPV4_HEADER) {
        return 0;
    }
    header->version_ihl = data[0];
    if ((header->version_ihl >> 4) != 4) {
        return 0;
    }
    header_length = (size_t)(header->version_ihl & 0x0f) * 4u;
    if (header_length < IPV4_HEADER || length < header_length) {
        return 0;
    }
    header->total_length = packet_read_u16(data + 2);
    header->identification = packet_read_u16(data + 4);
    header->flags_fragment = packet_read_u16(data + 6);
    header->ttl = data[8];
    header->protocol = data[9];
    header->checksum = packet_read_u16(data + 10);
    header->source = packet_read_u32(data + 12);
    header->destination = packet_read_u32(data + 16);
    return (int)header_length;
}

int packet_parse_tcp(const uint8_t *data, size_t length, tcp_header_t *header) {
    if (length < TCP_HEADER) {
        return 0;
    }
    header->source_port = packet_read_u16(data);
    header->destination_port = packet_read_u16(data + 2);
    header->sequence = packet_read_u32(data + 4);
    header->acknowledgement = packet_read_u32(data + 8);
    header->data_offset = data[12];
    header->flags = data[13];
    header->window = packet_read_u16(data + 14);
    header->checksum = packet_read_u16(data + 16);
    header->urgent = packet_read_u16(data + 18);
    return TCP_HEADER;
}

size_t packet_build_ipv4_tcp(uint8_t *buffer, size_t capacity, uint32_t source, uint32_t destination,
                             uint16_t source_port, uint16_t destination_port,
                             const uint8_t *payload, size_t payload_length) {
    size_t total = IPV4_HEADER + TCP_HEADER + payload_length;
    uint8_t *ip = buffer;
    uint8_t *tcp = buffer + IPV4_HEADER;
    if (capacity < total) {
        return 0;
    }
    memset(buffer, 0, total);
    ip[0] = 0x45;
    packet_write_u16(ip + 2, (uint16_t)total);
    ip[8] = 64;
    ip[9] = 6;
    packet_write_u32(ip + 12, source);
    packet_write_u32(ip + 16, destination);
    packet_write_u16(ip + 10, packet_checksum(ip, IPV4_HEADER));

    packet_write_u16(tcp, source_port);
    packet_write_u16(tcp + 2, destination_port);
    packet_write_u32(tcp + 4, 1);
    tcp[12] = 0x50;
    tcp[13] = 0x18;
    packet_write_u16(tcp + 14, 65535);
    if (payload_length > 0) {
        memcpy(tcp + TCP_HEADER, payload, payload_length);
    }
    return total;
}
