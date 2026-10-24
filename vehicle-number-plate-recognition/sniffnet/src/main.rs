use sniffnet::{parse_line, summarize, LiveCapture, Packet, Source, UdpSource};
use std::time::Duration;

const SAMPLE: &str = "\
# source, destination, protocol, bytes
10.0.0.1, 10.0.0.2, tcp, 1500
10.0.0.1, 10.0.0.2, tcp, 900
10.0.0.3, 8.8.8.8, udp, 120
10.0.0.2, 10.0.0.1, icmp, 64
10.0.0.3, 1.1.1.1, tcp, 2500
";

fn main() {
    let arguments: Vec<String> = std::env::args().collect();
    let mut live = false;
    let mut address = String::from("127.0.0.1:0");
    let mut file: Option<String> = None;

    let mut index = 1;
    while index < arguments.len() {
        match arguments[index].as_str() {
            "--live" => live = true,
            "--listen" => {
                index += 1;
                if index < arguments.len() {
                    address = arguments[index].clone();
                }
            }
            other => file = Some(other.to_string()),
        }
        index += 1;
    }

    if live {
        live_capture(&address);
        return;
    }

    let text = match file {
        Some(path) => std::fs::read_to_string(&path).unwrap_or_else(|error| {
            eprintln!("could not read {}: {}", path, error);
            std::process::exit(1);
        }),
        None => SAMPLE.to_string(),
    };

    let packets: Vec<_> = text.lines().filter_map(parse_line).collect();
    let summary = summarize(&packets);

    println!("packets: {}", summary.packets);
    println!("bytes:   {}", summary.bytes);
    println!("by protocol:");
    for (protocol, bytes) in &summary.by_protocol {
        println!("  {:<8} {}", protocol, bytes);
    }
    println!("top sources:");
    for (source, bytes) in &summary.top_sources {
        println!("  {:<15} {}", source, bytes);
    }
}

/// Listen on a socket and show the traffic while it comes in.
fn live_capture(address: &str) {
    let mut source = match UdpSource::bind(address) {
        Ok(source) => source,
        Err(error) => {
            eprintln!("could not listen on {}: {}", address, error);
            std::process::exit(1);
        }
    };
    let local = source
        .socket
        .local_addr()
        .map(|address| address.to_string())
        .unwrap_or_else(|_| address.to_string());
    println!("listening on {} - press Ctrl-C to stop", local);

    let mut capture = LiveCapture::new();
    let mut packets: Vec<Packet> = Vec::new();

    loop {
        // The datagrams that arrived are put in the capture and kept for
        // the summary.
        let mut taken = 0;
        while let Some(packet) = source.next_packet() {
            capture.push(packet.clone());
            packets.push(packet);
            taken += 1;
        }

        if taken > 0 {
            let _ = summarize(&packets);
            println!(
                "packets: {}  bytes: {}  busiest second: {}",
                capture.packets(),
                capture.bytes(),
                capture
                    .busiest_second()
                    .map(|sample| format!("{} bytes", sample.bytes))
                    .unwrap_or_else(|| "-".to_string())
            );
        }
        std::thread::sleep(Duration::from_millis(200));
    }
}
