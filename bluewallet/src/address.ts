/**
 * Address handling.
 *
 * A bech32 decoder (BIP-173) and the script hash an Electrum server indexes
 * a wallet by. Pure functions, no imports, so they can be unit tested.
 */

import { sha256HexReversed } from './sha256';

const CHARSET = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l';
const GENERATOR = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];

/** The bech32 checksum of a payload, for the given constant. */
function polymod(values: number[]): number {
  let chk = 1;
  for (const value of values) {
    const top = chk >>> 25;
    chk = ((chk & 0x1ffffff) << 5) ^ value;
    for (let i = 0; i < 5; i += 1) {
      if ((top >>> i) & 1) chk ^= GENERATOR[i];
    }
  }
  return chk;
}

function hrpExpand(hrp: string): number[] {
  const out: number[] = [];
  for (let i = 0; i < hrp.length; i += 1) out.push(hrp.charCodeAt(i) >>> 5);
  out.push(0);
  for (let i = 0; i < hrp.length; i += 1) out.push(hrp.charCodeAt(i) & 31);
  return out;
}

export type Bech32Decoded = {
  prefix: string;
  words: number[];
};

/** Decode a bech32 string, or return null when it is malformed. */
export function decodeBech32(address: string): Bech32Decoded | null {
  const trimmed = address.trim();
  if (trimmed.length < 8 || trimmed.length > 90) return null;

  const lower = trimmed.toLowerCase();
  if (lower !== trimmed && trimmed.toUpperCase() !== trimmed) return null;

  const separator = lower.lastIndexOf('1');
  if (separator === -1 || separator === 0 || separator + 7 > lower.length) return null;

  const prefix = lower.slice(0, separator);
  const payload = lower.slice(separator + 1);

  const words: number[] = [];
  for (const character of payload) {
    const index = CHARSET.indexOf(character);
    if (index === -1) return null;
    words.push(index);
  }

  if (polymod([...hrpExpand(prefix), ...words]) !== 1) return null;

  return { prefix, words: words.slice(0, -6) };
}


/**
 * The witness version and program of a decoded address.
 *
 * The first 5 bit word is the witness version, the rest is the program
 * converted back from 5 bit words to bytes. The padding bits at the end must
 * be zero, which is what BIP-173 requires.
 */
function witnessProgram(words: number[]): { version: number; bytes: number[] } | null {
  if (words.length < 2) return null;

  const version = words[0];
  let accumulator = 0;
  let bits = 0;
  const bytes: number[] = [];

  for (const word of words.slice(1)) {
    accumulator = (accumulator << 5) | word;
    bits += 5;
    while (bits >= 8) {
      bits -= 8;
      bytes.push((accumulator >>> bits) & 0xff);
    }
  }

  // The leftover bits are padding and have to be zero.
  if (bits > 0 && (accumulator & ((1 << bits) - 1)) !== 0) return null;

  return { version, bytes };
}

/** True when the string is a valid bech32 address. */
export function isValidBech32(address: string): boolean {
  return decodeBech32(address) !== null;
}

/** True when the string is a native segwit (bc1) address. */
export function isValidSegwitAddress(address: string): boolean {
  const decoded = decodeBech32(address);
  if (!decoded) return false;
  if (decoded.prefix !== 'bc') return false;

  const program = witnessProgram(decoded.words);
  if (!program) return false;

  // Only witness version 0 (the original segwit) is accepted: the script
  // hash an Electrum server uses is derived from it.
  if (program.version !== 0) return false;
  if (program.bytes.length !== 20 && program.bytes.length !== 32) return false;

  return true;
}

/** True when the address is a legacy base58 P2PKH or P2SH address. */
export function isValidBase58Address(address: string): boolean {
  const trimmed = address.trim();
  if (trimmed.length < 26 || trimmed.length > 35) return false;
  return /^[13mn2][1-9A-HJ-NP-Za-km-z]{25,34}$/.test(trimmed);
}

/** True when the address looks like something a Bitcoin wallet could send to. */
export function isValidAddress(address: string): boolean {
  return isValidSegwitAddress(address) || isValidBase58Address(address);
}

/**
 * The script hash an Electrum server indexes this address by.
 *
 * The hash is the SHA-256 of the output script, reversed and hex encoded.
 * Only native segwit (P2WPKH and P2WSH) is supported, which is what the app
 * shows.
 */
export function scriptHashFromSegwitAddress(address: string): string | null {
  const decoded = decodeBech32(address);
  if (!decoded || decoded.prefix !== 'bc') return null;

  const program = witnessProgram(decoded.words);
  if (!program) return null;
  if (program.version !== 0) return null;
  if (program.bytes.length !== 20 && program.bytes.length !== 32) return null;

  // OP_0 <push> <program>
  const script = new Uint8Array(2 + program.bytes.length);
  script[0] = 0x00;
  script[1] = program.bytes.length;
  script.set(program.bytes, 2);

  return sha256HexReversed(script);
}
