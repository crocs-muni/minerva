import java.math.BigInteger;
import java.security.NoSuchAlgorithmException;
import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.SignatureException;
import java.security.Provider;
import java.security.Security;
import java.security.Signature;
import java.security.KeyPairGenerator;
import java.security.KeyPair;
import java.security.interfaces.ECPublicKey;
import java.security.interfaces.ECPrivateKey;
import java.security.spec.ECGenParameterSpec;
import java.security.spec.ECPoint;
import java.security.spec.ECParameterSpec;
import java.util.Random;
import java.lang.System;
import sun.security.ec.SunEC;

class sunec_target {

    public static BigInteger[] asn1Parse(byte[] signature) {
        BigInteger r, s;
        int i = 0;
        if (signature[i++] != 0x30) {
            return null;
        }

        int seqValueLen = 0;
        if ((signature[i] & 0x80) == 0) {
            seqValueLen = signature[i++];
        } else {
            int seqLenLen = signature[i++] & 0x7f;
            while (seqLenLen > 0) {
                seqValueLen |= signature[i++] << (--seqLenLen);
            }
        }

        if (signature[i++] != 0x02) {
            return null;
        }
        int rLen = signature[i++];
        byte[] rData = new byte[rLen];
        System.arraycopy(signature, i, rData, 0, rLen);
        r = new BigInteger(1, rData);
        i += rLen;

        if (signature[i++] != 0x02) {
            return null;
        }
        int sLen = signature[i++];
        byte[] sData = new byte[sLen];
        System.arraycopy(signature, i, sData, 0, sLen);
        s = new BigInteger(1, sData);
        i += sLen;

        if (i != signature.length) {
            return null;
        }

        return new BigInteger[]{r, s};
    }

    public static void main(String[] args) throws NoSuchAlgorithmException, InvalidAlgorithmParameterException, InvalidKeyException, SignatureException {
        if (args.length != 3) {
            System.err.println("usage: sunec.jar <curve> <hash> <signature count>");
            System.exit(1);
        }
        String curveName = args[0];
        String hashName = args[1];
        int sigCount =  Integer.parseInt(args[2]);

        Provider prov = new SunEC();
        Security.addProvider(prov);

        String curves = prov.get("AlgorithmParameters.EC SupportedCurves").toString();
        String split[] = curves.split("\\|");
        String selected = null;
        for (String curve : split) {
            String body = curve.split(",")[0].substring(1);
            if (body.equals(curveName)) {
                selected = curve;
                break;
            }
        }
        if (selected == null) {
            System.err.println("Unknown curve: " + curveName);
            System.exit(3);
        }

        Random rand = new Random();
        byte data[] = new byte[64];
        rand.nextBytes(data);

        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC", prov);
        kpg.initialize(new ECGenParameterSpec(curveName));
        KeyPair kp = kpg.genKeyPair();
        ECPublicKey pubkey = (ECPublicKey) kp.getPublic();
        ECParameterSpec params = pubkey.getParams();
        int bytes = (params.getCurve().getField().getFieldSize() + 7) / 8;
        String coordFormat = "%0" + (bytes * 2) + "x";
        ECPoint q = pubkey.getW();
        System.out.print(String.format("04" + coordFormat + coordFormat + " ", q.getAffineX(), q.getAffineY()));

        for (int i = 0; i < 64; ++i) {
            System.out.print(String.format("%02x", data[i]));
        }

        if (System.getProperty("debug") != null) {
            ECPrivateKey privkey = (ECPrivateKey) kp.getPrivate();
            System.out.print(String.format(" %x", privkey.getS()));
        }

        System.out.println();

        Signature signer = Signature.getInstance(hashName.toUpperCase() + "withECDSA", prov);

        for (int i = 0; i < sigCount; ++i) {
            signer.initSign(kp.getPrivate());
            signer.update(data);
            long elapsed = -System.nanoTime();
            byte[] sig = signer.sign();
            elapsed += System.nanoTime();
            BigInteger[] parsed = asn1Parse(sig);

            System.out.println(String.format("%s,%s,%d", parsed[0].toString(16), parsed[1].toString(16), elapsed));
        }
    }
}