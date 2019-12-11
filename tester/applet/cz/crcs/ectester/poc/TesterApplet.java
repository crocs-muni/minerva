package cz.crcs.ectester.poc;

import javacard.framework.Applet;
import javacard.framework.APDU;
import javacard.framework.ISO7816;
import javacard.framework.ISOException;
import javacard.framework.JCSystem;
import javacard.framework.Util;
import javacard.security.KeyAgreement;
import javacard.security.KeyPair;
import javacard.security.ECPrivateKey;
import javacard.security.ECPublicKey;

public class TesterApplet extends Applet {
	public static final byte CLA_APPLET = (byte) 0xb0;
	public static final byte INS_PREPARE = (byte) 0x5a;
	public static final byte INS_KEX = (byte) 0x5b;

	private KeyPair keyPair = null;
	private ECPublicKey publicKey = null;
	private ECPrivateKey privateKey = null;
    private KeyAgreement kex = null;
    private byte[] ramArray = null;

	public static final byte ALG_EC_SVDP_DH = (byte) 1;
	
	public static final byte[] SECP256R1_P = new byte[]{
			(byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
			(byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x01,
			(byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00,
			(byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00,
			(byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00,
			(byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
			(byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
			(byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF
	};
    public static final byte[] SECP256R1_A = new byte[]{
            (byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
            (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x01,
            (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00,
            (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00,
            (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00,
            (byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
            (byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
            (byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFC
    };
    public static final byte[] SECP256R1_B = new byte[]{
            (byte) 0x5A, (byte) 0xC6, (byte) 0x35, (byte) 0xD8,
            (byte) 0xAA, (byte) 0x3A, (byte) 0x93, (byte) 0xE7,
            (byte) 0xB3, (byte) 0xEB, (byte) 0xBD, (byte) 0x55,
            (byte) 0x76, (byte) 0x98, (byte) 0x86, (byte) 0xBC,
            (byte) 0x65, (byte) 0x1D, (byte) 0x06, (byte) 0xB0,
            (byte) 0xCC, (byte) 0x53, (byte) 0xB0, (byte) 0xF6,
            (byte) 0x3B, (byte) 0xCE, (byte) 0x3C, (byte) 0x3E,
            (byte) 0x27, (byte) 0xD2, (byte) 0x60, (byte) 0x4B
    };
	public static final byte[] SECP256R1_G = new byte[]{
			(byte) 0x04,
            (byte) 0x6B, (byte) 0x17, (byte) 0xD1, (byte) 0xF2,
            (byte) 0xE1, (byte) 0x2C, (byte) 0x42, (byte) 0x47,
            (byte) 0xF8, (byte) 0xBC, (byte) 0xE6, (byte) 0xE5,
            (byte) 0x63, (byte) 0xA4, (byte) 0x40, (byte) 0xF2,
            (byte) 0x77, (byte) 0x03, (byte) 0x7D, (byte) 0x81,
            (byte) 0x2D, (byte) 0xEB, (byte) 0x33, (byte) 0xA0,
            (byte) 0xF4, (byte) 0xA1, (byte) 0x39, (byte) 0x45,
            (byte) 0xD8, (byte) 0x98, (byte) 0xC2, (byte) 0x96,
            (byte) 0x4F, (byte) 0xE3, (byte) 0x42, (byte) 0xE2,
            (byte) 0xFE, (byte) 0x1A, (byte) 0x7F, (byte) 0x9B,
            (byte) 0x8E, (byte) 0xE7, (byte) 0xEB, (byte) 0x4A,
            (byte) 0x7C, (byte) 0x0F, (byte) 0x9E, (byte) 0x16,
            (byte) 0x2B, (byte) 0xCE, (byte) 0x33, (byte) 0x57,
            (byte) 0x6B, (byte) 0x31, (byte) 0x5E, (byte) 0xCE,
            (byte) 0xCB, (byte) 0xB6, (byte) 0x40, (byte) 0x68,
            (byte) 0x37, (byte) 0xBF, (byte) 0x51, (byte) 0xF5
    };
    public static final byte[] SECP256R1_R = new byte[]{
            (byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
            (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00,
            (byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
            (byte) 0xFF, (byte) 0xFF, (byte) 0xFF, (byte) 0xFF,
            (byte) 0xBC, (byte) 0xE6, (byte) 0xFA, (byte) 0xAD,
            (byte) 0xA7, (byte) 0x17, (byte) 0x9E, (byte) 0x84,
            (byte) 0xF3, (byte) 0xB9, (byte) 0xCA, (byte) 0xC2,
            (byte) 0xFC, (byte) 0x63, (byte) 0x25, (byte) 0x51
    };
	public static final short SECP256R1_K = 1;


	protected TesterApplet(byte[] buffer, short offset, byte length) {
		kex = KeyAgreement.getInstance(ALG_EC_SVDP_DH, false);
		ramArray = JCSystem.makeTransientByteArray((short) 32, JCSystem.CLEAR_ON_RESET);
		register();
	}

	public void process(APDU apdu) throws ISOException {
		byte[] apduBuffer = apdu.getBuffer();
		byte cla = apduBuffer[ISO7816.OFFSET_CLA];
		byte ins = apduBuffer[ISO7816.OFFSET_INS];

		if (selectingApplet()) {
			return;
		}

		if (cla == CLA_APPLET) {
			short len = 0;
			if (ins == INS_PREPARE) {
				len = prepare(apdu);
			} else if (ins == INS_KEX) {
				len = kex(apdu);
			} else {
				ISOException.throwIt(ISO7816.SW_INS_NOT_SUPPORTED);
			}
			apdu.setOutgoingAndSend((short)0, len);
		} else {
			ISOException.throwIt(ISO7816.SW_CLA_NOT_SUPPORTED);
		}
	}

	private short prepare(APDU apdu) {
	    if (JCSystem.isObjectDeletionSupported()) {
	        JCSystem.requestObjectDeletion();
	    }

		keyPair = new KeyPair(KeyPair.ALG_EC_FP, (short) 256);
		publicKey = (ECPublicKey) keyPair.getPublic();
		privateKey = (ECPrivateKey) keyPair.getPrivate();
		publicKey.setFieldFP(SECP256R1_P, (short) 0, (short) SECP256R1_P.length);
		privateKey.setFieldFP(SECP256R1_P, (short) 0, (short) SECP256R1_P.length);
		
		publicKey.setA(SECP256R1_A, (short) 0, (short) SECP256R1_A.length);
		privateKey.setA(SECP256R1_A, (short) 0, (short) SECP256R1_A.length);
		
		publicKey.setB(SECP256R1_B, (short) 0, (short) SECP256R1_B.length);
		privateKey.setB(SECP256R1_B, (short) 0, (short) SECP256R1_B.length);
		
		publicKey.setG(SECP256R1_G, (short) 0, (short) SECP256R1_G.length);
		privateKey.setG(SECP256R1_G, (short) 0, (short) SECP256R1_G.length);
		
		publicKey.setR(SECP256R1_R, (short) 0, (short) SECP256R1_R.length);
		privateKey.setR(SECP256R1_R, (short) 0, (short) SECP256R1_R.length);
		
		publicKey.setK(SECP256R1_K);
		privateKey.setK(SECP256R1_K);

		byte[] apdubuf = apdu.getBuffer();
		apdu.setIncomingAndReceive();

		Util.arrayFillNonAtomic(ramArray, (short) 0, (short) 32, (byte) 0);
		short bits = (short) (apdubuf[ISO7816.OFFSET_P1] & 0xff);
        short bytes = (short) ((short) (bits + 8) / 8);
        byte bm8 = (byte) (bits % 8);
        byte value = (byte) (1 << bm8);
        ramArray[(short) (32 - bytes)] = value;
        privateKey.setS(ramArray, (short) 0, (short) 32);
		return 0;
	}

	private short kex(APDU apdu) {
		if (keyPair == null || !privateKey.isInitialized()) {
			ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
		}
		byte[] apdubuf = apdu.getBuffer();
		apdu.setIncomingAndReceive();

        kex.init(privateKey);
        kex.generateSecret(SECP256R1_G, (short) 0, (short) 65, ramArray, (short) 0);
        return 0;
	}

	public static void install(byte[] bArray, short bOffset, byte bLength) throws ISOException {
		new TesterApplet(bArray, bOffset, bLength);
	}
}
