package main

import (
	"flag"
	"fmt"
	"net"
	"os"
)

func main() {
	secret := flag.String("secret", "correct horse battery staple", "shared passphrase")
	message := flag.String("message", "hello from the tunnel", "payload to send")
	flag.Parse()

	key := DeriveKey(*secret)
	left, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer left.Close()
	right, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer right.Close()

	switching := NewSwitch()
	switching.Register(10, left, key)
	switching.Register(20, right, key)

	if err := switching.Send(Packet{Src: 10, Dst: 20, Payload: []byte(*message)}); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	packet, _, err := ReadFrom(right, key)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("received %q from virtual ip %d\n", packet.Payload, packet.Src)
}
