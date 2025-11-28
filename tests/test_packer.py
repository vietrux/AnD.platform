# test_packer module
"""Tests for packer functionality."""

import os
import struct
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.packer import (
    ENCRYPTABLE_SECTIONS,
    CertificateError,
    EncryptionError,
    PackerError,
    PEInfo,
    PEParseError,
    PESection,
    SigningError,
    aes_encrypt_data,
    calculate_entropy,
    encrypt_pe_sections,
    generate_loader_stub,
    generate_selfsigned_cert,
    get_packer_info,
    load_config,
    manipulate_entropy,
    pack_pe,
    parse_pe,
    parse_pe_bytes,
    sign_binary,
    xor_encrypt_data,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def xor_key() -> bytes:
    """XOR encryption key for testing."""
    return b"testkey1234567890"


@pytest.fixture
def aes_key() -> bytes:
    """AES-256 encryption key for testing."""
    return os.urandom(32)


@pytest.fixture
def sample_pe_data() -> bytes:
    """Create a minimal valid PE structure for testing."""
    # DOS header (64 bytes)
    dos_header = bytearray(64)
    dos_header[0:2] = b"MZ"  # DOS signature
    dos_header[0x3C:0x40] = struct.pack("<I", 64)  # PE offset at byte 64

    # PE signature
    pe_sig = b"PE\x00\x00"

    # COFF header (20 bytes)
    coff_header = bytearray(20)
    struct.pack_into("<H", coff_header, 0, 0x8664)  # AMD64 machine
    struct.pack_into("<H", coff_header, 2, 2)  # 2 sections
    struct.pack_into("<H", coff_header, 16, 112)  # Optional header size

    # Optional header (112 bytes for PE32+)
    optional_header = bytearray(112)
    struct.pack_into("<H", optional_header, 0, 0x20B)  # PE32+ magic
    struct.pack_into("<I", optional_header, 16, 0x1000)  # Entry point
    struct.pack_into("<Q", optional_header, 24, 0x140000000)  # Image base

    # Section headers (2 sections, 40 bytes each)
    # .text section
    text_section = bytearray(40)
    text_section[0:5] = b".text"
    struct.pack_into("<I", text_section, 8, 0x100)  # Virtual size
    struct.pack_into("<I", text_section, 12, 0x1000)  # Virtual address
    struct.pack_into("<I", text_section, 16, 0x100)  # Raw size
    struct.pack_into("<I", text_section, 20, 0x200)  # Raw offset
    struct.pack_into("<I", text_section, 36, 0x60000020)  # Characteristics

    # .data section
    data_section = bytearray(40)
    data_section[0:5] = b".data"
    struct.pack_into("<I", data_section, 8, 0x80)  # Virtual size
    struct.pack_into("<I", data_section, 12, 0x2000)  # Virtual address
    struct.pack_into("<I", data_section, 16, 0x80)  # Raw size
    struct.pack_into("<I", data_section, 20, 0x300)  # Raw offset
    struct.pack_into("<I", data_section, 36, 0xC0000040)  # Characteristics

    # Section data
    text_data = b"\x90" * 0x100  # NOP sled for .text
    data_data = b"\x00" * 0x80  # Zero bytes for .data

    # Assemble PE
    pe_data = bytes(dos_header) + pe_sig + bytes(coff_header) + bytes(optional_header)
    pe_data += bytes(text_section) + bytes(data_section)

    # Pad to raw offset of .text
    pe_data = pe_data.ljust(0x200, b"\x00")
    pe_data += text_data

    # Pad to raw offset of .data
    pe_data = pe_data.ljust(0x300, b"\x00")
    pe_data += data_data

    return pe_data


@pytest.fixture
def sample_pe_file(sample_pe_data: bytes, tmp_path: Path) -> Path:
    """Create a temporary PE file for testing."""
    pe_path = tmp_path / "test.exe"
    pe_path.write_bytes(sample_pe_data)
    return pe_path


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


# =============================================================================
# Tests for xor_encrypt_data
# =============================================================================


class TestXorEncryptData:
    """Tests for XOR data encryption."""

    def test_basic_encryption(self, xor_key: bytes) -> None:
        """Test basic XOR encryption."""
        data = b"Hello, World!"
        encrypted = xor_encrypt_data(data, xor_key)

        assert encrypted != data
        assert len(encrypted) == len(data)

    def test_encryption_is_reversible(self, xor_key: bytes) -> None:
        """Test that XOR encryption is reversible."""
        data = b"Test data for XOR encryption"
        encrypted = xor_encrypt_data(data, xor_key)
        decrypted = xor_encrypt_data(encrypted, xor_key)

        assert decrypted == data

    def test_empty_key_raises_error(self) -> None:
        """Test that empty key raises EncryptionError."""
        with pytest.raises(EncryptionError) as exc_info:
            xor_encrypt_data(b"test", b"")
        assert "empty" in str(exc_info.value).lower()

    def test_key_cycling(self) -> None:
        """Test that key is cycled for longer data."""
        key = b"AB"
        data = b"XXXX"
        encrypted = xor_encrypt_data(data, key)

        # 'X' XOR 'A' and 'X' XOR 'B' should alternate
        expected = bytes([
            ord('X') ^ ord('A'),
            ord('X') ^ ord('B'),
            ord('X') ^ ord('A'),
            ord('X') ^ ord('B'),
        ])
        assert encrypted == expected


# =============================================================================
# Tests for aes_encrypt_data
# =============================================================================


class TestAesEncryptData:
    """Tests for AES data encryption."""

    def test_basic_encryption(self, aes_key: bytes) -> None:
        """Test basic AES encryption."""
        data = b"Hello, World!"
        encrypted = aes_encrypt_data(data, aes_key)

        # Should have IV (16 bytes) + padded ciphertext
        assert len(encrypted) >= 16 + len(data)

    def test_invalid_key_length(self) -> None:
        """Test that non-32-byte key raises EncryptionError."""
        with pytest.raises(EncryptionError) as exc_info:
            aes_encrypt_data(b"test", b"shortkey")
        assert "32" in str(exc_info.value)

    def test_different_ivs(self, aes_key: bytes) -> None:
        """Test that each encryption uses different IV."""
        data = b"same data"
        encrypted1 = aes_encrypt_data(data, aes_key)
        encrypted2 = aes_encrypt_data(data, aes_key)

        # First 16 bytes (IV) should be different
        assert encrypted1[:16] != encrypted2[:16]

    def test_output_format(self, aes_key: bytes) -> None:
        """Test that output is IV + ciphertext."""
        data = b"Test message"
        encrypted = aes_encrypt_data(data, aes_key)

        # IV is 16 bytes, ciphertext is padded to 16-byte blocks
        iv = encrypted[:16]
        assert len(iv) == 16
        # Ciphertext should be multiple of 16 (AES block size)
        ciphertext_len = len(encrypted) - 16
        assert ciphertext_len % 16 == 0


# =============================================================================
# Tests for parse_pe_bytes
# =============================================================================


class TestParsePeBytes:
    """Tests for PE parsing."""

    def test_parse_valid_pe(self, sample_pe_data: bytes) -> None:
        """Test parsing a valid PE."""
        pe_info = parse_pe_bytes(sample_pe_data)

        assert pe_info.is_64bit
        assert pe_info.entry_point == 0x1000
        assert pe_info.image_base == 0x140000000
        assert len(pe_info.sections) == 2

    def test_parse_sections(self, sample_pe_data: bytes) -> None:
        """Test that sections are parsed correctly."""
        pe_info = parse_pe_bytes(sample_pe_data)

        # Find .text section
        text_section = next(s for s in pe_info.sections if s.name == b".text")
        assert text_section.virtual_size == 0x100
        assert text_section.raw_size == 0x100
        assert len(text_section.data) == 0x100

        # Find .data section
        data_section = next(s for s in pe_info.sections if s.name == b".data")
        assert data_section.virtual_size == 0x80
        assert data_section.raw_size == 0x80

    def test_invalid_dos_signature(self) -> None:
        """Test that invalid DOS signature raises error."""
        with pytest.raises(PEParseError) as exc_info:
            parse_pe_bytes(b"XX" + b"\x00" * 62)
        assert "DOS" in str(exc_info.value)

    def test_invalid_pe_signature(self) -> None:
        """Test that invalid PE signature raises error."""
        # Valid DOS header pointing to invalid PE
        data = b"MZ" + b"\x00" * 58 + struct.pack("<I", 64) + b"XX\x00\x00"
        with pytest.raises(PEParseError) as exc_info:
            parse_pe_bytes(data)
        assert "PE" in str(exc_info.value)

    def test_truncated_data(self) -> None:
        """Test that truncated data raises error."""
        with pytest.raises(PEParseError):
            parse_pe_bytes(b"MZ" + b"\x00" * 10)


class TestParsePe:
    """Tests for PE file parsing."""

    def test_parse_file(self, sample_pe_file: Path) -> None:
        """Test parsing a PE file."""
        pe_info = parse_pe(sample_pe_file)

        assert pe_info.is_64bit
        assert len(pe_info.sections) == 2

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Test that missing file raises error."""
        with pytest.raises(PEParseError) as exc_info:
            parse_pe(tmp_path / "nonexistent.exe")
        assert "not found" in str(exc_info.value)


# =============================================================================
# Tests for encrypt_pe_sections
# =============================================================================


class TestEncryptPeSections:
    """Tests for PE section encryption."""

    def test_encrypt_sections(self, sample_pe_file: Path, xor_key: bytes) -> None:
        """Test encrypting PE sections."""
        encrypted_data = encrypt_pe_sections(sample_pe_file, xor_key, "xor")

        # Parse both original and encrypted
        original = parse_pe(sample_pe_file)
        encrypted = parse_pe_bytes(encrypted_data)

        # .text section should be different
        orig_text = next(s for s in original.sections if s.name == b".text")
        enc_text = next(s for s in encrypted.sections if s.name == b".text")
        assert orig_text.data != enc_text.data

    def test_encrypt_with_aes(self, sample_pe_file: Path, aes_key: bytes) -> None:
        """Test encrypting PE sections with AES."""
        encrypted_data = encrypt_pe_sections(sample_pe_file, aes_key, "aes256")

        assert len(encrypted_data) > 0

    def test_encrypt_specific_sections(
        self, sample_pe_file: Path, xor_key: bytes
    ) -> None:
        """Test encrypting only specific sections."""
        encrypted_data = encrypt_pe_sections(
            sample_pe_file, xor_key, "xor", sections_to_encrypt={b".text"}
        )

        # Parse both
        original = parse_pe(sample_pe_file)
        encrypted = parse_pe_bytes(encrypted_data)

        # .text should be encrypted
        orig_text = next(s for s in original.sections if s.name == b".text")
        enc_text = next(s for s in encrypted.sections if s.name == b".text")
        assert orig_text.data != enc_text.data

        # .data should be unchanged
        orig_data = next(s for s in original.sections if s.name == b".data")
        enc_data_section = next(s for s in encrypted.sections if s.name == b".data")
        assert orig_data.data == enc_data_section.data

    def test_file_not_found(self, tmp_path: Path, xor_key: bytes) -> None:
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            encrypt_pe_sections(tmp_path / "nonexistent.exe", xor_key)


# =============================================================================
# Tests for generate_loader_stub
# =============================================================================


class TestGenerateLoaderStub:
    """Tests for loader stub generation."""

    def test_generate_xor_stub(self, xor_key: bytes) -> None:
        """Test generating XOR loader stub."""
        stub = generate_loader_stub(xor_key, "xor")

        assert isinstance(stub, bytes)
        assert len(stub) > 0
        # Should contain key data
        assert len(stub) >= len(xor_key)

    def test_generate_aes_stub(self, aes_key: bytes) -> None:
        """Test generating AES loader stub."""
        stub = generate_loader_stub(aes_key, "aes256")

        assert isinstance(stub, bytes)
        assert len(stub) > 0

    def test_invalid_algorithm(self, xor_key: bytes) -> None:
        """Test that invalid algorithm raises error."""
        with pytest.raises(PackerError):
            generate_loader_stub(xor_key, "invalid")  # type: ignore[arg-type]

    def test_stub_contains_registers(self, xor_key: bytes) -> None:
        """Test that stub contains register operations."""
        stub = generate_loader_stub(xor_key, "xor")

        # Should contain push/pop opcodes
        assert 0x50 in stub or 0x51 in stub  # push rax/rcx


# =============================================================================
# Tests for calculate_entropy
# =============================================================================


class TestCalculateEntropy:
    """Tests for entropy calculation."""

    def test_zero_entropy(self) -> None:
        """Test that uniform data has low entropy."""
        data = b"\x00" * 1000
        entropy = calculate_entropy(data)
        assert entropy == 0.0

    def test_single_byte_entropy(self) -> None:
        """Test entropy of single repeated byte."""
        data = b"A" * 1000
        entropy = calculate_entropy(data)
        assert entropy == 0.0

    def test_max_entropy(self) -> None:
        """Test that random data has high entropy."""
        data = os.urandom(10000)
        entropy = calculate_entropy(data)
        # Random data should have entropy close to 8.0
        assert 7.0 < entropy <= 8.0

    def test_known_entropy(self) -> None:
        """Test entropy of known distribution."""
        # Two bytes, equal frequency
        data = b"AB" * 1000
        entropy = calculate_entropy(data)
        # Should be close to 1.0 (log2(2))
        assert 0.9 < entropy < 1.1

    def test_empty_data(self) -> None:
        """Test entropy of empty data."""
        entropy = calculate_entropy(b"")
        assert entropy == 0.0

    def test_all_bytes(self) -> None:
        """Test entropy when all byte values present equally."""
        data = bytes(range(256)) * 100
        entropy = calculate_entropy(data)
        # Should be close to 8.0 (log2(256))
        assert 7.9 < entropy <= 8.0


# =============================================================================
# Tests for manipulate_entropy
# =============================================================================


class TestManipulateEntropy:
    """Tests for entropy manipulation."""

    def test_reduce_entropy(self, sample_pe_file: Path, temp_dir: Path) -> None:
        """Test reducing entropy of a file."""
        output_path = temp_dir / "reduced.exe"

        # Create high-entropy data file
        high_entropy_path = temp_dir / "high_entropy.exe"
        high_entropy_path.write_bytes(os.urandom(1000))

        original_entropy = calculate_entropy(high_entropy_path.read_bytes())

        manipulate_entropy(high_entropy_path, target_entropy=4.0, output_path=output_path)

        new_entropy = calculate_entropy(output_path.read_bytes())
        assert new_entropy < original_entropy

    def test_already_low_entropy(self, temp_dir: Path) -> None:
        """Test with already low entropy file."""
        low_entropy_path = temp_dir / "low_entropy.exe"
        low_entropy_path.write_bytes(b"\x00" * 1000)

        output_path = temp_dir / "output.exe"
        manipulate_entropy(low_entropy_path, target_entropy=6.0, output_path=output_path)

        # Output should exist
        assert output_path.exists()

    def test_inplace_modification(self, temp_dir: Path) -> None:
        """Test in-place entropy manipulation."""
        test_file = temp_dir / "test.exe"
        test_file.write_bytes(os.urandom(1000))

        original_size = test_file.stat().st_size

        manipulate_entropy(test_file, target_entropy=4.0)

        # File should be larger due to padding
        new_size = test_file.stat().st_size
        assert new_size >= original_size


# =============================================================================
# Tests for sign_binary
# =============================================================================


class TestSignBinary:
    """Tests for binary signing."""

    def test_no_signing_tool(self, sample_pe_file: Path, temp_dir: Path) -> None:
        """Test error when no signing tool is available."""
        # Create dummy certificate file first
        cert_path = temp_dir / "cert.pfx"
        cert_path.write_bytes(b"dummy cert")

        with patch("shutil.which", return_value=None):
            with pytest.raises(SigningError) as exc_info:
                sign_binary(sample_pe_file, cert_path, "password")
            assert "No signing tool" in str(exc_info.value)

    def test_missing_pe_file(self, temp_dir: Path) -> None:
        """Test error when PE file doesn't exist."""
        with pytest.raises(SigningError) as exc_info:
            sign_binary(temp_dir / "nonexistent.exe", temp_dir / "cert.pfx", "password")
        assert "not found" in str(exc_info.value)

    def test_missing_certificate(self, sample_pe_file: Path, temp_dir: Path) -> None:
        """Test error when certificate doesn't exist."""
        with pytest.raises(SigningError) as exc_info:
            sign_binary(sample_pe_file, temp_dir / "nonexistent.pfx", "password")
        assert "not found" in str(exc_info.value)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_osslsigncode_success(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        sample_pe_file: Path,
        temp_dir: Path,
    ) -> None:
        """Test successful signing with osslsigncode."""
        mock_which.side_effect = lambda x: "/usr/bin/osslsigncode" if x == "osslsigncode" else None
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Create dummy certificate
        cert_path = temp_dir / "test.pfx"
        cert_path.write_bytes(b"dummy cert")

        result = sign_binary(sample_pe_file, cert_path, "password")
        assert result is True

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_osslsigncode_failure(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        sample_pe_file: Path,
        temp_dir: Path,
    ) -> None:
        """Test signing failure with osslsigncode."""
        mock_which.side_effect = lambda x: "/usr/bin/osslsigncode" if x == "osslsigncode" else None
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="signing failed")

        cert_path = temp_dir / "test.pfx"
        cert_path.write_bytes(b"dummy cert")

        with pytest.raises(SigningError) as exc_info:
            sign_binary(sample_pe_file, cert_path, "password")
        assert "failed" in str(exc_info.value).lower()


# =============================================================================
# Tests for generate_selfsigned_cert
# =============================================================================


class TestGenerateSelfsignedCert:
    """Tests for self-signed certificate generation."""

    def test_generate_cert(self, temp_dir: Path) -> None:
        """Test generating a self-signed certificate."""
        try:
            pfx_path, password = generate_selfsigned_cert(output_dir=temp_dir)

            assert Path(pfx_path).exists()
            assert len(password) > 0
            assert Path(pfx_path).suffix == ".pfx"
        except CertificateError as e:
            if "cryptography" in str(e):
                pytest.skip("cryptography package not installed")
            raise

    def test_custom_parameters(self, temp_dir: Path) -> None:
        """Test certificate with custom parameters."""
        try:
            pfx_path, password = generate_selfsigned_cert(
                common_name="Test Corp",
                organization="Test Organization",
                country="DE",
                valid_days=30,
                output_dir=temp_dir,
            )

            assert Path(pfx_path).exists()
        except CertificateError as e:
            if "cryptography" in str(e):
                pytest.skip("cryptography package not installed")
            raise

    def test_cert_file_content(self, temp_dir: Path) -> None:
        """Test that generated certificate has valid content."""
        try:
            pfx_path, password = generate_selfsigned_cert(output_dir=temp_dir)

            # PFX file should have some content
            content = Path(pfx_path).read_bytes()
            assert len(content) > 100  # Should be a reasonable size
        except CertificateError as e:
            if "cryptography" in str(e):
                pytest.skip("cryptography package not installed")
            raise


# =============================================================================
# Tests for pack_pe
# =============================================================================


class TestPackPe:
    """Tests for full PE packing pipeline."""

    def test_basic_packing(
        self, sample_pe_file: Path, temp_dir: Path, xor_key: bytes
    ) -> None:
        """Test basic PE packing."""
        output_path = temp_dir / "packed.exe"

        result = pack_pe(
            sample_pe_file,
            output_path,
            key=xor_key,
            algorithm="xor",
            encrypt_sections=True,
            reduce_entropy=False,
            sign=False,
        )

        assert result["success"]
        assert output_path.exists()
        assert result["key"] == xor_key

    def test_packing_with_entropy_reduction(
        self, sample_pe_file: Path, temp_dir: Path, xor_key: bytes
    ) -> None:
        """Test PE packing with entropy reduction."""
        output_path = temp_dir / "packed.exe"

        result = pack_pe(
            sample_pe_file,
            output_path,
            key=xor_key,
            algorithm="xor",
            encrypt_sections=True,
            reduce_entropy=True,
            target_entropy=5.0,
            sign=False,
        )

        assert result["success"]
        assert result["final_entropy"] <= result["original_entropy"] or result["original_entropy"] < 5.0

    def test_packing_generates_key(
        self, sample_pe_file: Path, temp_dir: Path
    ) -> None:
        """Test that packing generates key if not provided."""
        output_path = temp_dir / "packed.exe"

        result = pack_pe(
            sample_pe_file,
            output_path,
            key=None,
            algorithm="xor",
            encrypt_sections=True,
            reduce_entropy=False,
            sign=False,
        )

        assert result["success"]
        assert result["key"] is not None
        assert len(result["key"]) == 16  # Default XOR key length

    def test_packing_aes_key_length(
        self, sample_pe_file: Path, temp_dir: Path
    ) -> None:
        """Test that AES packing generates 32-byte key."""
        output_path = temp_dir / "packed.exe"

        result = pack_pe(
            sample_pe_file,
            output_path,
            key=None,
            algorithm="aes256",
            encrypt_sections=True,
            reduce_entropy=False,
            sign=False,
        )

        assert result["success"]
        assert len(result["key"]) == 32


# =============================================================================
# Tests for get_packer_info
# =============================================================================


class TestGetPackerInfo:
    """Tests for packer info retrieval."""

    def test_info_structure(self) -> None:
        """Test packer info structure."""
        info = get_packer_info()

        assert "supported_algorithms" in info
        assert "xor" in info["supported_algorithms"]
        assert "aes256" in info["supported_algorithms"]

        assert "encryptable_sections" in info
        assert ".text" in info["encryptable_sections"]
        assert ".data" in info["encryptable_sections"]

        assert "signing_tools" in info
        assert "crypto_available" in info

    def test_encryptable_sections_match(self) -> None:
        """Test that info matches ENCRYPTABLE_SECTIONS constant."""
        info = get_packer_info()

        for section in ENCRYPTABLE_SECTIONS:
            assert section.decode() in info["encryptable_sections"]


# =============================================================================
# Tests for load_config
# =============================================================================


class TestLoadConfig:
    """Tests for configuration loading."""

    def test_load_default_config(self) -> None:
        """Test loading default config.yaml."""
        # This should work if config.yaml exists in project root
        try:
            config = load_config()
            assert "packer" in config
            assert "signing" in config
        except PackerError:
            # Config file might not exist in test environment
            pass

    def test_missing_config(self, temp_dir: Path) -> None:
        """Test error when config file is missing."""
        with pytest.raises(PackerError) as exc_info:
            load_config(temp_dir / "nonexistent.yaml")
        assert "not found" in str(exc_info.value)

    def test_invalid_yaml(self, temp_dir: Path) -> None:
        """Test error when config file is invalid YAML."""
        invalid_config = temp_dir / "invalid.yaml"
        invalid_config.write_text("invalid: yaml: content: [")

        with pytest.raises(PackerError) as exc_info:
            load_config(invalid_config)
        assert "parse" in str(exc_info.value).lower()


# =============================================================================
# Tests for PESection and PEInfo dataclasses
# =============================================================================


class TestDataclasses:
    """Tests for dataclass structures."""

    def test_pe_section_creation(self) -> None:
        """Test PESection dataclass creation."""
        section = PESection(
            name=b".text",
            virtual_size=0x1000,
            virtual_address=0x1000,
            raw_size=0x800,
            raw_offset=0x200,
            characteristics=0x60000020,
            data=b"\x90" * 0x800,
        )

        assert section.name == b".text"
        assert section.virtual_size == 0x1000
        assert len(section.data) == 0x800

    def test_pe_info_creation(self) -> None:
        """Test PEInfo dataclass creation."""
        pe_info = PEInfo(
            dos_header=b"MZ" + b"\x00" * 62,
            pe_offset=64,
            pe_header=b"PE\x00\x00" + b"\x00" * 20,
            optional_header=b"\x00" * 112,
            sections=[],
            is_64bit=True,
            entry_point=0x1000,
            image_base=0x140000000,
        )

        assert pe_info.is_64bit
        assert pe_info.entry_point == 0x1000
        assert pe_info.image_base == 0x140000000


# =============================================================================
# Tests for Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_encrypt_empty_section(self, temp_dir: Path, xor_key: bytes) -> None:
        """Test encrypting PE with empty section."""
        # Create PE with empty .data section
        dos_header = bytearray(64)
        dos_header[0:2] = b"MZ"
        dos_header[0x3C:0x40] = struct.pack("<I", 64)

        pe_sig = b"PE\x00\x00"

        coff_header = bytearray(20)
        struct.pack_into("<H", coff_header, 0, 0x8664)
        struct.pack_into("<H", coff_header, 2, 1)
        struct.pack_into("<H", coff_header, 16, 112)

        optional_header = bytearray(112)
        struct.pack_into("<H", optional_header, 0, 0x20B)

        # Section with zero raw size
        section = bytearray(40)
        section[0:5] = b".data"
        struct.pack_into("<I", section, 16, 0)  # Raw size = 0

        pe_data = bytes(dos_header) + pe_sig + bytes(coff_header)
        pe_data += bytes(optional_header) + bytes(section)

        pe_path = temp_dir / "empty_section.exe"
        pe_path.write_bytes(pe_data)

        # Should not raise error
        encrypted = encrypt_pe_sections(pe_path, xor_key, "xor")
        assert len(encrypted) > 0

    def test_very_short_key(self) -> None:
        """Test XOR encryption with single-byte key."""
        key = b"X"
        data = b"Hello, World!"
        encrypted = xor_encrypt_data(data, key)

        # Should XOR every byte with 'X'
        expected = bytes(b ^ ord('X') for b in data)
        assert encrypted == expected

    def test_entropy_precision(self) -> None:
        """Test entropy calculation precision."""
        # Known entropy for 2 equally distributed values
        data = bytes([0, 1] * 5000)
        entropy = calculate_entropy(data)

        # Should be very close to 1.0
        assert abs(entropy - 1.0) < 0.01
