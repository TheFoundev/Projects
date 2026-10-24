use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Protocol {
    Tcp,
    Udp,
    Icmp,
    Other(String),
}

impl Protocol {
    pub fn parse(text: &str) -> Protocol {
        match text.trim().to_lowercase().as_str() {
            "tcp" => Protocol::Tcp,
            "udp" => Protocol::Udp,
            "icmp" => Protocol::Icmp,
            other => Protocol::Other(other.to_string()),
        }
    }

    pub fn label(&self) -> String {
        match self {
            Protocol::Tcp => "tcp".to_string(),
            Protocol::Udp => "udp".to_string(),
            Protocol::Icmp => "icmp".to_string(),
            Protocol::Other(name) => name.clone(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Packet {
    pub source: String,
    pub destination: String,
    pub protocol: Protocol,
    pub bytes: u64,
}

pub fn parse_line(line: &str) -> Option<Packet> {
    let trimmed = line.trim();
    if trimmed.is_empty() || trimmed.starts_with('#') {
        return None;
    }
    let parts: Vec<&str> = trimmed.split(',').map(|part| part.trim()).collect();
    if parts.len() < 4 {
        return None;
    }
    let bytes = parts[3].parse::<u64>().ok()?;
    Some(Packet {
        source: parts[0].to_string(),
        destination: parts[1].to_string(),
        protocol: Protocol::parse(parts[2]),
        bytes,
    })
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Summary {
    pub packets: u64,
    pub bytes: u64,
    pub by_protocol: Vec<(String, u64)>,
    pub top_sources: Vec<(String, u64)>,
}

pub fn summarize(packets: &[Packet]) -> Summary {
    let mut protocols: BTreeMap<String, u64> = BTreeMap::new();
    let mut sources: BTreeMap<String, u64> = BTreeMap::new();
    let mut total_bytes = 0;
    for packet in packets {
        total_bytes += packet.bytes;
        *protocols.entry(packet.protocol.label()).or_insert(0) += packet.bytes;
        *sources.entry(packet.source.clone()).or_insert(0) += packet.bytes;
    }

    let mut by_protocol: Vec<(String, u64)> = protocols.into_iter().collect();
    by_protocol.sort_by(|left, right| right.1.cmp(&left.1).then(left.0.cmp(&right.0)));

    let mut top_sources: Vec<(String, u64)> = sources.into_iter().collect();
    top_sources.sort_by(|left, right| right.1.cmp(&left.1).then(left.0.cmp(&right.0)));
    top_sources.truncate(5);

    Summary {
        packets: packets.len() as u64,
        bytes: total_bytes,
        by_protocol,
        top_sources,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_a_valid_line() {
        let packet = parse_line("10.0.0.1, 10.0.0.2, TCP, 1500").expect("packet");
        assert_eq!(packet.source.as_str(), "10.0.0.1");
        assert_eq!(packet.destination.as_str(), "10.0.0.2");
        assert_eq!(packet.protocol, Protocol::Tcp);
        assert_eq!(packet.bytes, 1500);
    }

    #[test]
    fn skips_comments_and_bad_lines() {
        assert!(parse_line("# a comment").is_none());
        assert!(parse_line("").is_none());
        assert!(parse_line("only,three,fields").is_none());
        assert!(parse_line("a, b, tcp, not-a-number").is_none());
    }

    #[test]
    fn summarises_protocols_and_sources() {
        let packets = vec![
            parse_line("a, b, tcp, 100").unwrap(),
            parse_line("a, c, udp, 50").unwrap(),
            parse_line("d, c, tcp, 25").unwrap(),
        ];
        let summary = summarize(&packets);
        assert_eq!(summary.packets, 3);
        assert_eq!(summary.bytes, 175);
        assert_eq!(summary.by_protocol[0], ("tcp".to_string(), 125));
        assert_eq!(summary.by_protocol[1], ("udp".to_string(), 50));
        assert_eq!(summary.top_sources[0], ("a".to_string(), 150));
    }
}

// ---------------------------------------------------------------------------
// The live capture
// ---------------------------------------------------------------------------

use std::collections::VecDeque;
use std::net::UdpSocket;
use std::time::Duration;

/// A source of packets.
///
/// The trait is what makes the capture live: a source gives one packet at a
/// time, so the program can show the traffic while it comes in.
pub trait Source {
    /// The next packet, or None when there is nothing at the moment.
    fn next_packet(&mut self) -> Option<Packet>;
}

/// A source that reads the packets out of a text capture, the way the
/// parser does.
pub struct TextSource {
    lines: VecDeque<String>,
}

impl TextSource {
    /// A source over the lines of a capture.
    pub fn new<I: IntoIterator<Item = String>>(lines: I) -> TextSource {
        TextSource {
            lines: lines.into_iter().collect(),
        }
    }
}

impl Source for TextSource {
    fn next_packet(&mut self) -> Option<Packet> {
        while let Some(line) = self.lines.pop_front() {
            if let Some(packet) = parse_line(&line) {
                return Some(packet);
            }
        }
        None
    }
}

/// A source that listens on a udp socket.
///
/// This is a real live capture: the datagrams that arrive on the socket
/// become packets, with the address they came from and how many bytes they
/// carry.
pub struct UdpSource {
    /// The socket the datagrams arrive on.
    pub socket: UdpSocket,
    buffer: [u8; 65535],
}

impl UdpSource {
    /// A source that listens on the address.
    pub fn bind(address: &str) -> std::io::Result<UdpSource> {
        let socket = UdpSocket::bind(address)?;
        socket.set_read_timeout(Some(Duration::from_millis(250)))?;
        Ok(UdpSource {
            socket,
            buffer: [0; 65535],
        })
    }
}

impl Source for UdpSource {
    fn next_packet(&mut self) -> Option<Packet> {
        match self.socket.recv_from(&mut self.buffer) {
            Ok((count, from)) => Some(Packet {
                source: from.ip().to_string(),
                destination: self.socket.local_addr().map(|a| a.ip().to_string()).unwrap_or_default(),
                protocol: Protocol::Udp,
                bytes: count as u64,
            }),
            Err(_) => None,
        }
    }
}

/// One moment of the capture.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Sample {
    /// The seconds since the capture started.
    pub second: u64,
    /// The packets of that second.
    pub packets: u64,
    /// The bytes of that second.
    pub bytes: u64,
}

/// The traffic of a capture, second by second.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct LiveCapture {
    samples: Vec<Sample>,
    packets: u64,
    bytes: u64,
    second: u64,
}

impl LiveCapture {
    /// A capture that has not seen anything yet.
    pub fn new() -> LiveCapture {
        LiveCapture::default()
    }

    /// The samples of the capture, the oldest first.
    pub fn samples(&self) -> &[Sample] {
        &self.samples
    }

    /// The number of packets so far.
    pub fn packets(&self) -> u64 {
        self.packets
    }

    /// The number of bytes so far.
    pub fn bytes(&self) -> u64 {
        self.bytes
    }

    /// The busiest second so far.
    pub fn busiest_second(&self) -> Option<&Sample> {
        self.samples.iter().max_by_key(|sample| sample.bytes)
    }

    /// Put one packet in the capture.
    pub fn push(&mut self, packet: Packet) {
        self.packets += 1;
        self.bytes += packet.bytes;

        let second = self.seconds();
        match self.samples.last_mut() {
            Some(sample) if sample.second == second => {
                sample.packets += 1;
                sample.bytes += packet.bytes;
            }
            _ => self.samples.push(Sample {
                second,
                packets: 1,
                bytes: packet.bytes,
            }),
        }
    }

    /// Take the packets of a source and put them in the capture.
    ///
    /// The source is read until it has nothing at the moment, so the caller
    /// can call it again and again and see the traffic grow.
    pub fn collect(&mut self, source: &mut dyn Source) -> usize {
        let mut taken = 0;
        while let Some(packet) = source.next_packet() {
            self.push(packet);
            taken += 1;
        }
        taken
    }

    /// The second the capture is in.
    fn seconds(&self) -> u64 {
        self.second
    }

    /// Move the capture on to the next second.
    pub fn tick(&mut self) {
        self.second += 1;
    }
}

#[cfg(test)]
mod live_tests {
    use super::*;

    #[test]
    fn a_text_source_gives_the_packets() {
        let mut source = TextSource::new(vec![
            "a, b, tcp, 100".to_string(),
            "# a comment".to_string(),
            "c, d, udp, 50".to_string(),
        ]);

        assert_eq!(source.next_packet().map(|p| p.bytes), Some(100));
        assert_eq!(source.next_packet().map(|p| p.bytes), Some(50));
        assert!(source.next_packet().is_none());
    }

    #[test]
    fn the_capture_counts_the_packets_and_the_bytes() {
        let mut source = TextSource::new(vec![
            "a, b, tcp, 100".to_string(),
            "c, d, udp, 50".to_string(),
        ]);
        let mut capture = LiveCapture::new();

        let taken = capture.collect(&mut source);

        assert_eq!(taken, 2);
        assert_eq!(capture.packets(), 2);
        assert_eq!(capture.bytes(), 150);
        assert_eq!(capture.samples().len(), 1);
        assert_eq!(capture.samples()[0].bytes, 150);
    }

    #[test]
    fn the_capture_makes_a_sample_for_every_second() {
        let mut first = TextSource::new(vec!["a, b, tcp, 100".to_string()]);
        let mut second = TextSource::new(vec!["c, d, udp, 50".to_string()]);
        let mut capture = LiveCapture::new();

        capture.collect(&mut first);
        capture.tick();
        capture.collect(&mut second);

        assert_eq!(capture.samples().len(), 2);
        assert_eq!(capture.samples()[0].second, 0);
        assert_eq!(capture.samples()[1].second, 1);
        assert_eq!(capture.busiest_second().map(|s| s.second), Some(0));
    }

    #[test]
    fn a_udp_source_receives_a_datagram() {
        let source = match UdpSource::bind("127.0.0.1:0") {
            Ok(source) => source,
            Err(_) => return,
        };
        let address = source.socket.local_addr().expect("address");
        let sender = UdpSocket::bind("127.0.0.1:0").expect("sender");
        sender.send_to(b"hello", address).expect("send");

        let mut source = source;
        // The datagram may take a moment to arrive.
        for _ in 0..40 {
            if let Some(packet) = source.next_packet() {
                assert_eq!(packet.bytes, 5);
                assert_eq!(packet.protocol, Protocol::Udp);
                return;
            }
            std::thread::sleep(Duration::from_millis(25));
        }
        panic!("the datagram did not arrive");
    }
}
