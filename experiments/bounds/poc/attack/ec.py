"""
This module is a collection of modules glued together, to provide basic
elliptic curve arithmetic for curves over prime and binary fields. It consists of
 - tinyec: https://github.com/alexmgr/tinyec (GPL v3 licensed)
 - pyfinite: https://github.com/emin63/pyfinite (MIT licensed)
 - modular square root from https://eli.thegreenplace.net/2009/03/07/computing-modular-square-roots-in-python
 - and some of my own code: https://github.com/J08nY
"""

import abc
import random
from functools import reduce, wraps

PRIME_FIELD = {
    "brainpoolP160r1": {
        "p": 0xE95E4A5F737059DC60DFC7AD95B3D8139515620F,
        "a": 0x340E7BE2A280EB74E2BE61BADA745D97E8F7C300,
        "b": 0x1E589A8595423412134FAA2DBDEC95C8D8675E58,
        "g": (0xBED5AF16EA3F6A4F62938C4631EB5AF7BDBCDBC3,
              0x1667CB477A1A8EC338F94741669C976316DA6321),
        "n": 0xE95E4A5F737059DC60DF5991D45029409E60FC09,
        "h": 0x1},
    "brainpoolP192r1": {
        "p": 0xC302F41D932A36CDA7A3463093D18DB78FCE476DE1A86297,
        "a": 0x6A91174076B1E0E19C39C031FE8685C1CAE040E5C69A28EF,
        "b": 0x469A28EF7C28CCA3DC721D044F4496BCCA7EF4146FBF25C9,
        "g": (0xC0A0647EAAB6A48753B033C56CB0F0900A2F5C4853375FD6,
              0x14B690866ABD5BB88B5F4828C1490002E6773FA2FA299B8F),
        "n": 0xC302F41D932A36CDA7A3462F9E9E916B5BE8F1029AC4ACC1,
        "h": 0x1},
    "brainpoolP224r1": {
        "p": 0xD7C134AA264366862A18302575D1D787B09F075797DA89F57EC8C0FF,
        "a": 0x68A5E62CA9CE6C1C299803A6C1530B514E182AD8B0042A59CAD29F43,
        "b": 0x2580F63CCFE44138870713B1A92369E33E2135D266DBB372386C400B,
        "g": (0x0D9029AD2C7E5CF4340823B2A87DC68C9E4CE3174C1E6EFDEE12C07D,
              0x58AA56F772C0726F24C6B89E4ECDAC24354B9E99CAA3F6D3761402CD),
        "n": 0xD7C134AA264366862A18302575D0FB98D116BC4B6DDEBCA3A5A7939F,
        "h": 0x1},
    "brainpoolP256r1": {
        "p": 0xA9FB57DBA1EEA9BC3E660A909D838D726E3BF623D52620282013481D1F6E5377,
        "a": 0x7D5A0975FC2C3057EEF67530417AFFE7FB8055C126DC5C6CE94A4B44F330B5D9,
        "b": 0x26DC5C6CE94A4B44F330B5D9BBD77CBF958416295CF7E1CE6BCCDC18FF8C07B6,
        "g": (0x8BD2AEB9CB7E57CB2C4B482FFC81B7AFB9DE27E1E3BD23C23A4453BD9ACE3262,
              0x547EF835C3DAC4FD97F8461A14611DC9C27745132DED8E545C1D54C72F046997),
        "n": 0xA9FB57DBA1EEA9BC3E660A909D838D718C397AA3B561A6F7901E0E82974856A7,
        "h": 0x1},
    "brainpoolP320r1": {
        "p": 0xD35E472036BC4FB7E13C785ED201E065F98FCFA6F6F40DEF4F92B9EC7893EC28FCD412B1F1B32E27,
        "a": 0x3EE30B568FBAB0F883CCEBD46D3F3BB8A2A73513F5EB79DA66190EB085FFA9F492F375A97D860EB4,
        "b": 0x520883949DFDBC42D3AD198640688A6FE13F41349554B49ACC31DCCD884539816F5EB4AC8FB1F1A6,
        "g": (
            0x43BD7E9AFB53D8B85289BCC48EE5BFE6F20137D10A087EB6E7871E2A10A599C710AF8D0D39E20611,
            0x14FDD05545EC1CC8AB4093247F77275E0743FFED117182EAA9C77877AAAC6AC7D35245D1692E8EE1),
        "n": 0xD35E472036BC4FB7E13C785ED201E065F98FCFA5B68F12A32D482EC7EE8658E98691555B44C59311,
        "h": 0x1},
    "brainpoolP384r1": {
        "p": 0x8CB91E82A3386D280F5D6F7E50E641DF152F7109ED5456B412B1DA197FB71123ACD3A729901D1A71874700133107EC53,
        "a": 0x7BC382C63D8C150C3C72080ACE05AFA0C2BEA28E4FB22787139165EFBA91F90F8AA5814A503AD4EB04A8C7DD22CE2826,
        "b": 0x04A8C7DD22CE28268B39B55416F0447C2FB77DE107DCD2A62E880EA53EEB62D57CB4390295DBC9943AB78696FA504C11,
        "g": (
            0x1D1C64F068CF45FFA2A63A81B7C13F6B8847A3E77EF14FE3DB7FCAFE0CBD10E8E826E03436D646AAEF87B2E247D4AF1E,
            0x8ABE1D7520F9C2A45CB1EB8E95CFD55262B70B29FEEC5864E19C054FF99129280E4646217791811142820341263C5315),
        "n": 0x8CB91E82A3386D280F5D6F7E50E641DF152F7109ED5456B31F166E6CAC0425A7CF3AB6AF6B7FC3103B883202E9046565,
        "h": 0x1},
    "brainpoolP512r1": {
        "p": 0xAADD9DB8DBE9C48B3FD4E6AE33C9FC07CB308DB3B3C9D20ED6639CCA703308717D4D9B009BC66842AECDA12AE6A380E62881FF2F2D82C68528AA6056583A48F3,
        "a": 0x7830A3318B603B89E2327145AC234CC594CBDD8D3DF91610A83441CAEA9863BC2DED5D5AA8253AA10A2EF1C98B9AC8B57F1117A72BF2C7B9E7C1AC4D77FC94CA,
        "b": 0x3DF91610A83441CAEA9863BC2DED5D5AA8253AA10A2EF1C98B9AC8B57F1117A72BF2C7B9E7C1AC4D77FC94CADC083E67984050B75EBAE5DD2809BD638016F723,
        "g": (
            0x81AEE4BDD82ED9645A21322E9C4C6A9385ED9F70B5D916C1B43B62EEF4D0098EFF3B1F78E2D0D48D50D1687B93B97D5F7C6D5047406A5E688B352209BCB9F822,
            0x7DDE385D566332ECC0EABFA9CF7822FDF209F70024A57B1AA000C55B881F8111B2DCDE494A5F485E5BCA4BD88A2763AED1CA2B2FA8F0540678CD1E0F3AD80892),
        "n": 0xAADD9DB8DBE9C48B3FD4E6AE33C9FC07CB308DB3B3C9D20ED6639CCA70330870553E5C414CA92619418661197FAC10471DB1D381085DDADDB58796829CA90069,
        "h": 0x1},
    "secp192r1": {
        "p": 0xfffffffffffffffffffffffffffffffeffffffffffffffff,
        "a": 0xfffffffffffffffffffffffffffffffefffffffffffffffc,
        "b": 0x64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1,
        "g": (0x188da80eb03090f67cbf20eb43a18800f4ff0afd82ff1012,
              0x07192b95ffc8da78631011ed6b24cdd573f977a11e794811),
        "n": 0xffffffffffffffffffffffff99def836146bc9b1b4d22831,
        "h": 0x1},
    "secp224r1": {
        "p": 0xffffffffffffffffffffffffffffffff000000000000000000000001,
        "a": 0xfffffffffffffffffffffffffffffffefffffffffffffffffffffffe,
        "b": 0xb4050a850c04b3abf54132565044b0b7d7bfd8ba270b39432355ffb4,
        "g": (0xb70e0cbd6bb4bf7f321390b94a03c1d356c21122343280d6115c1d21,
              0xbd376388b5f723fb4c22dfe6cd4375a05a07476444d5819985007e34),
        "n": 0xffffffffffffffffffffffffffff16a2e0b8f03e13dd29455c5c2a3d,
        "h": 0x1},
    "secp256r1": {
        "p": 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff,
        "a": 0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc,
        "b": 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b,
        "g": (0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
              0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5),
        "n": 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551,
        "h": 0x1},
    "secp384r1": {
        "p": 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffeffffffff0000000000000000ffffffff,
        "a": 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffeffffffff0000000000000000fffffffc,
        "b": 0xb3312fa7e23ee7e4988e056be3f82d19181d9c6efe8141120314088f5013875ac656398d8a2ed19d2a85c8edd3ec2aef,
        "g": (
            0xaa87ca22be8b05378eb1c71ef320ad746e1d3b628ba79b9859f741e082542a385502f25dbf55296c3a545e3872760ab7,
            0x3617de4a96262c6f5d9e98bf9292dc29f8f41dbd289a147ce9da3113b5f0b8c00a60b1ce1d7e819d7a431d7c90ea0e5f),
        "n": 0xffffffffffffffffffffffffffffffffffffffffffffffffc7634d81f4372ddf581a0db248b0a77aecec196accc52973,
        "h": 0x1},
    "secp521r1": {
        "p": 0x000001ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        "a": 0x000001fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc,
        "b": 0x00000051953eb9618e1c9a1f929a21a0b68540eea2da725b99b315f3b8b489918ef109e156193951ec7e937b1652c0bd3bb1bf073573df883d2c34f1ef451fd46b503f00,
        "g": (
            0x000000c6858e06b70404e9cd9e3ecb662395b4429c648139053fb521f828af606b4d3dbaa14b5e77efe75928fe1dc127a2ffa8de3348b3c1856a429bf97e7e31c2e5bd66,
            0x0000011839296a789a3bc0045c8a5fb42c7d1bd998f54449579b446817afbd17273e662c97ee72995ef42640c550b9013fad0761353c7086a272c24088be94769fd16650),
        "n": 0x000001fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa51868783bf2f966b7fcc0148f709a5d03bb5c9b8899c47aebb6fb71e91386409,
        "h": 0x1}}

BINARY_FIELD = {
    "sect163r1": {
        "poly": (0xa3, 0x07, 0x06, 0x03, 0),
        "a": 0x07b6882caaefa84f9554ff8428bd88e246d2782ae2,
        "b": 0x0713612dcddcb40aab946bda29ca91f73af958afd9,
        "g": (0x0369979697ab43897789566789567f787a7876a654,
              0x00435edb42efafb2989d51fefce3c80988f41ff883),
        "n": 0x03ffffffffffffffffffff48aab689c29ca710279b,
        "h": 0x2},
    "sect233r1": {
        "poly": (0xe9, 0x4a, 0),
        "a": 1,
        "b": 0x0066647ede6c332c7f8c0923bb58213b333b20e9ce4281fe115f7d8f90ad,
        "g": (0x00fac9dfcbac8313bb2139f1bb755fef65bc391f8b36f8f8eb7371fd558b,
              0x01006a08a41903350678e58528bebf8a0beff867a7ca36716f7e01f81052),
        "n": 0x01000000000000000000000000000013e974e72f8a6922031d2603cfe0d7,
        "h": 0x2},
    "sect283r1": {
        "poly": (0x011b, 0x0c, 0x07, 0x05, 0),
        "a": 1,
        "b": 0x027b680ac8b8596da5a4af8a19a0303fca97fd7645309fa2a581485af6263e313b79a2f5,
        "g": (0x05f939258db7dd90e1934f8c70b0dfec2eed25b8557eac9c80e2e198f8cdbecd86b12053,
              0x03676854fe24141cb98fe6d4b20d02b4516ff702350eddb0826779c813f0df45be8112f4),
        "n": 0x03ffffffffffffffffffffffffffffffffffef90399660fc938a90165b042a7cefadb307,
        "h": 0x2
    },
    "sect409r1": {
        "poly": (0x0199, 0x57, 0),
        "a": 1,
        "b": 0x0021a5c2c8ee9feb5c4b9a753b7b476b7fd6422ef1f3dd674761fa99d6ac27c8a9a197b272822f6cd57a55aa4f50ae317b13545f,
        "g": (
            0x015d4860d088ddb3496b0c6064756260441cde4af1771d4db01ffe5b34e59703dc255a868a1180515603aeab60794e54bb7996a7,
            0x0061b1cfab6be5f32bbfa78324ed106a7636b9c5a7bd198d0158aa4f5488d08f38514f1fdf4b4f40d2181b3681c364ba0273c706),
        "n": 0x010000000000000000000000000000000000000000000000000001e2aad6a612f33307be5fa47c3c9e052f838164cd37d9a21173,
        "h": 0x2
    },
    "sect571r1": {
        "poly": (0x023b, 0x0a, 0x05, 0x02, 0),
        "a": 1,
        "b": 0x02f40e7e2221f295de297117b7f3d62f5c6a97ffcb8ceff1cd6ba8ce4a9a18ad84ffabbd8efa59332be7ad6756a66e294afd185a78ff12aa520e4de739baca0c7ffeff7f2955727a,
        "g": (
            0x0303001d34b856296c16c0d40d3cd7750a93d1d2955fa80aa5f40fc8db7b2abdbde53950f4c0d293cdd711a35b67fb1499ae60038614f1394abfa3b4c850d927e1e7769c8eec2d19,
            0x037bf27342da639b6dccfffeb73d69d78c6c27a6009cbbca1980f8533921e8a684423e43bab08a576291af8f461bb2a8b3531d2f0485c19b16e2f1516e23dd3c1a4827af1b8ac15b),
        "n": 0x03ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe661ce18ff55987308059b186823851ec7dd9ca1161de93d5174d66e8382e9bb2fe84e47,
        "h": 0x2
    }
}


def legendre_symbol(a, p):
    """ Compute the Legendre symbol a|p using
        Euler's criterion. p is a prime, a is
        relatively prime to p (if p divides
        a, then a|p = 0)

        Returns 1 if a has a square root modulo
        p, -1 otherwise.
    """
    ls = pow(a, (p - 1) // 2, p)
    return -1 if ls == p - 1 else ls


def is_prime(n, trials=50):
    """
    Miller-Rabin primality test.
    """
    s = 0
    d = n - 1
    while d % 2 == 0:
        d >>= 1
        s += 1
    assert (2 ** s * d == n - 1)

    def trial_composite(a):
        if pow(a, d, n) == 1:
            return False
        for i in range(s):
            if pow(a, 2 ** i * d, n) == n - 1:
                return False
        return True

    for i in range(trials):  # number of trials
        a = random.randrange(2, n)
        if trial_composite(a):
            return False
    return True


def gcd(a, b):
    """Euclid's greatest common denominator algorithm."""
    if abs(a) < abs(b):
        return gcd(b, a)

    while abs(b) > 0:
        q, r = divmod(a, b)
        a, b = b, r

    return a


def extgcd(a, b):
    """Extended Euclid's greatest common denominator algorithm."""
    if abs(b) > abs(a):
        (x, y, d) = extgcd(b, a)
        return y, x, d

    if abs(b) == 0:
        return 1, 0, a

    x1, x2, y1, y2 = 0, 1, 1, 0
    while abs(b) > 0:
        q, r = divmod(a, b)
        x = x2 - q * x1
        y = y2 - q * y1
        a, b, x2, x1, y2, y1 = b, r, x1, x, y1, y

    return x2, y2, a


def check(func):
    @wraps(func)
    def method(self, other):
        if isinstance(other, int):
            other = self.__class__(other, self.field)
        if type(self) is type(other):
            if self.field == other.field:
                return func(self, other)
            else:
                raise ValueError
        else:
            raise TypeError

    return method


class Mod(object):
    """An element x of ℤₙ."""

    def __init__(self, x: int, n: int):
        self.x = x % n
        self.field = n

    @check
    def __add__(self, other):
        return Mod((self.x + other.x) % self.field, self.field)

    @check
    def __radd__(self, other):
        return self + other

    @check
    def __sub__(self, other):
        return Mod((self.x - other.x) % self.field, self.field)

    @check
    def __rsub__(self, other):
        return -self + other

    def __neg__(self):
        return Mod(self.field - self.x, self.field)

    def inverse(self):
        x, y, d = extgcd(self.x, self.field)
        return Mod(x, self.field)

    def __invert__(self):
        return self.inverse()

    @check
    def __mul__(self, other):
        return Mod((self.x * other.x) % self.field, self.field)

    @check
    def __rmul__(self, other):
        return self * other

    @check
    def __truediv__(self, other):
        return self * ~other

    @check
    def __rtruediv__(self, other):
        return ~self * other

    @check
    def __floordiv__(self, other):
        return self * ~other

    @check
    def __rfloordiv__(self, other):
        return ~self * other

    @check
    def __div__(self, other):
        return self.__floordiv__(other)

    @check
    def __rdiv__(self, other):
        return self.__rfloordiv__(other)

    @check
    def __divmod__(self, divisor):
        q, r = divmod(self.x, divisor.x)
        return Mod(q, self.field), Mod(r, self.field)

    def __int__(self):
        return self.x

    def __eq__(self, other):
        if type(other) is not Mod:
            return False
        return self.x == other.x and self.field == other.field

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return str(self.x)

    def __pow__(self, n):
        if not isinstance(n, int):
            raise TypeError
        if n == 0:
            return Mod(1, self.field)
        if n < 0:
            return (~self) ** -n
        if n == 1:
            return self
        if n == 2:
            return self * self

        q = self
        r = self if n & 1 else Mod(1, self.field)

        i = 2
        while i <= n:
            q = (q * q)
            if n & i == i:
                r = (q * r)
            i = i << 1
        return r

    def sqrt(self):
        if not is_prime(self.field):
            raise NotImplementedError
        # Simple cases
        if legendre_symbol(self.x, self.field) != 1 or self.x == 0 or self.field == 2:
            raise ValueError("Not a quadratic residue.")
        if self.field % 4 == 3:
            return self ** ((self.field + 1) // 4)

        a = self.x
        p = self.field
        s = p - 1
        e = 0
        while s % 2 == 0:
            s /= 2
            e += 1

        n = 2
        while legendre_symbol(n, p) != -1:
            n += 1

        x = pow(a, (s + 1) / 2, p)
        b = pow(a, s, p)
        g = pow(n, s, p)
        r = e

        while True:
            t = b
            m = 0
            for m in range(r):
                if t == 1:
                    break
                t = pow(t, 2, p)

            if m == 0:
                return Mod(x, p)

            gs = pow(g, 2 ** (r - m - 1), p)
            g = (gs * gs) % p
            x = (x * gs) % p
            b = (b * g) % p
            r = m


class FField(object):
    """
    The FField class implements a binary field.
    """

    def __init__(self, n, gen):
        """
        This method constructs the field GF(2^n).  It takes two
        required arguments, n and gen,
        representing the coefficients of the generator polynomial
        (of degree n) to use.
        Note that you can look at the generator for the field object
        F by looking at F.generator.
        """

        self.n = n
        if len(gen) != n + 1:
            full_gen = [0] * (n + 1)
            for i in gen:
                full_gen[i] = 1
            gen = full_gen[::-1]
        self.generator = self.to_element(gen)
        self.unity = 1

    def add(self, x, y):
        """
        Adds two field elements and returns the result.
        """

        return x ^ y

    def subtract(self, x, y):
        """
        Subtracts the second argument from the first and returns
        the result.  In fields of characteristic two this is the same
        as the Add method.
        """
        return x ^ y

    def multiply(self, f, v):
        """
        Multiplies two field elements (modulo the generator
        self.generator) and returns the result.

        See MultiplyWithoutReducing if you don't want multiplication
        modulo self.generator.
        """
        m = self.multiply_no_reduce(f, v)
        return self.full_division(m, self.generator, self.find_degree(m), self.n)[1]

    def inverse(self, f):
        """
        Computes the multiplicative inverse of its argument and
        returns the result.
        """
        return self.ext_gcd(self.unity, f, self.generator, self.find_degree(f), self.n)[1]

    def divide(self, f, v):
        """
        Divide(f,v) returns f * v^-1.
        """
        return self.multiply(f, self.inverse(v))

    def exponentiate(self, f, n):
        """
        Exponentiate(f, n) returns f^n.
        """
        if not isinstance(n, int):
            raise TypeError
        if n == 0:
            return self.unity
        if n < 0:
            f = self.inverse(f)
            n = -n
        if n == 1:
            return f
        if n == 2:
            return self.multiply(f, f)

        q = f
        r = f if n & 1 else self.unity

        i = 2
        while i <= n:
            q = self.multiply(q, q)
            if n & i == i:
                r = self.multiply(q, r)
            i = i << 1
        return r

    def sqrt(self, f):
        return self.exponentiate(f, (2 ** self.n) - 1)

    def trace(self, f):
        t = f
        for _ in range(1, self.n):
            t = self.add(self.multiply(t, t), f)
        return t

    def half_trace(self, f):
        if self.n % 2 != 1:
            raise ValueError
        h = f
        for _ in range(1, (self.n - 1) // 2):
            h = self.multiply(h, h)
            h = self.add(self.multiply(h, h), f)
        return h

    def find_degree(self, v):
        """
        Find the degree of the polynomial representing the input field
        element v.  This takes O(degree(v)) operations.

        A faster version requiring only O(log(degree(v)))
        could be written using binary search...
        """
        if v:
            return v.bit_length() - 1
        else:
            return 0

    def multiply_no_reduce(self, f, v):
        """
        Multiplies two field elements and does not take the result
        modulo self.generator.  You probably should not use this
        unless you know what you are doing; look at Multiply instead.
        """

        result = 0
        mask = self.unity
        for i in range(self.n + 1):
            if mask & v:
                result = result ^ f
            f = f << 1
            mask = mask << 1
        return result

    def ext_gcd(self, d, a, b, a_degree, b_degree):
        """
        Takes arguments (d,a,b,aDegree,bDegree) where d = gcd(a,b)
        and returns the result of the extended Euclid algorithm
        on (d,a,b).
        """
        if b == 0:
            return a, self.unity, 0
        else:
            (floorADivB, aModB) = self.full_division(a, b, a_degree, b_degree)
            (d, x, y) = self.ext_gcd(d, b, aModB, b_degree, self.find_degree(aModB))
            return d, y, self.subtract(x, self.multiply(floorADivB, y))

    def full_division(self, f, v, f_degree, v_degree):
        """
        Takes four arguments, f, v, fDegree, and vDegree where
        fDegree and vDegree are the degrees of the field elements
        f and v represented as a polynomials.
        This method returns the field elements a and b such that

            f(x) = a(x) * v(x) + b(x).

        That is, a is the divisor and b is the remainder, or in
        other words a is like floor(f/v) and b is like f modulo v.
        """

        result = 0
        mask = self.unity << f_degree
        for i in range(f_degree, v_degree - 1, -1):
            if mask & f:
                result = result ^ (self.unity << (i - v_degree))
                f = self.subtract(f, v << (i - v_degree))
            mask = mask >> self.unity
        return result, f

    def coefficients(self, f):
        """
        Show coefficients of input field element represented as a
        polynomial in decreasing order.
        """

        result = []
        for i in range(self.n, -1, -1):
            if (self.unity << i) & f:
                result.append(1)
            else:
                result.append(0)

        return result

    def polynomial(self, f):
        """
        Show input field element represented as a polynomial.
        """

        f_degree = self.find_degree(f)
        result = ''

        if f == 0:
            return '0'

        for i in range(f_degree, 0, -1):
            if (1 << i) & f:
                result = result + (' x^' + repr(i))
        if 1 & f:
            result = result + ' ' + repr(1)
        return result.strip().replace(' ', ' + ')

    def to_element(self, l):
        """
        This method takes as input a binary list (e.g. [1, 0, 1, 1])
        and converts it to a decimal representation of a field element.
        For example, [1, 0, 1, 1] is mapped to 8 | 2 | 1 = 11.

        Note if the input list is of degree >= to the degree of the
        generator for the field, then you will have to call take the
        result modulo the generator to get a proper element in the
        field.
        """

        temp = map(lambda a, b: a << b, l, range(len(l) - 1, -1, -1))
        return reduce(lambda a, b: a | b, temp)

    def __str__(self):
        return "F_(2^{}): {}".format(self.n, self.polynomial(self.generator))

    def __repr__(self):
        return str(self)


class FElement(object):
    """
    This class provides field elements which overload the
    +,-,*,%,//,/ operators to be the appropriate field operation.
    Note that before creating FElement objects you must first
    create an FField object.
    """

    def __init__(self, f, field):
        """
        The constructor takes two arguments, field, and e where
        field is an FField object and e is an integer representing
        an element in FField.

        The result is a new FElement instance.
        """
        self.f = f
        self.field = field

    @check
    def __add__(self, other):
        return FElement(self.field.add(self.f, other.f), self.field)

    @check
    def __sub__(self, other):
        return FElement(self.field.add(self.f, other.f), self.field)

    def __neg__(self):
        return self

    @check
    def __mul__(self, other):
        return FElement(self.field.multiply(self.f, other.f), self.field)

    @check
    def __floordiv__(self, o):
        return FElement(self.field.full_division(self.f, o.f,
                                                 self.field.find_degree(self.f),
                                                 self.field.find_degree(o.f))[0], self.field)

    @check
    def __truediv__(self, other):
        return FElement(self.field.divide(self.f, other.f), self.field)

    def __div__(self, *args, **kwargs):
        return self.__truediv__(*args, **kwargs)

    @check
    def __divmod__(self, other):
        d, m = self.field.full_division(self.f, other.f,
                                        self.field.find_degree(self.f),
                                        self.field.find_degree(other.f))
        return FElement(d, self.field), FElement(m, self.field)

    def inverse(self):
        return FElement(self.field.inverse(self.f), self.field)

    def __invert__(self):
        return self.inverse()

    def sqrt(self):
        return FElement(self.field.sqrt(self.f), self.field)

    def trace(self):
        return FElement(self.field.trace(self.f), self.field)

    def half_trace(self):
        return FElement(self.field.half_trace(self.f), self.field)

    def __pow__(self, power, modulo=None):
        return FElement(self.field.exponentiate(self.f, power), self.field)

    def __str__(self):
        return str(int(self))

    def __repr__(self):
        return str(self)

    def __int__(self):
        return self.f

    def __eq__(self, other):
        if not isinstance(other, FElement):
            return False
        if self.field != other.field:
            return False
        return self.f == other.f


class Curve(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, field, a, b, group, name="undefined"):
        self.field = field
        self.name = name
        self.a = a
        self.b = b
        self.group = group
        self.g = Point(self, self.group.g[0], self.group.g[1])

    @abc.abstractmethod
    def is_singular(self):
        ...

    @abc.abstractmethod
    def on_curve(self, x, y):
        ...

    @abc.abstractmethod
    def add(self, x1, y1, x2, y2):
        ...

    @abc.abstractmethod
    def dbl(self, x, y):
        ...

    @abc.abstractmethod
    def neg(self, x, y):
        ...

    @abc.abstractmethod
    def encode_point(self, point, compressed=False):
        ...

    @abc.abstractmethod
    def decode_point(self, byte_data):
        ...

    def bit_size(self):
        return self.group.n.bit_length()

    def byte_size(self):
        return (self.bit_size() + 7) // 8

    @abc.abstractmethod
    def field_size(self):
        ...

    def __eq__(self, other):
        if not isinstance(other, Curve):
            return False
        return self.field == other.field and self.a == other.a and self.b == other.b and self.group == other.group

    def __repr__(self):
        return str(self)


class CurveFp(Curve):
    def is_singular(self):
        return (4 * self.a ** 3 + 27 * self.b ** 2) == 0

    def on_curve(self, x, y):
        return (y ** 2 - x ** 3 - self.a * x - self.b) == 0

    def add(self, x1, y1, x2, y2):
        lm = (y2 - y1) / (x2 - x1)
        x3 = lm ** 2 - x1 - x2
        y3 = lm * (x1 - x3) - y1
        return x3, y3

    def dbl(self, x, y):
        lm = (3 * x ** 2 + self.a) / (2 * y)
        x3 = lm ** 2 - (2 * x)
        y3 = lm * (x - x3) - y
        return x3, y3

    def mul(self, k, x, y, z=1):
        def _add(x1, y1, z1, x2, y2, z2):
            yz = y1 * z2
            xz = x1 * z2
            zz = z1 * z2
            u = y2 * z1 - yz
            uu = u ** 2
            v = x2 * z1 - xz
            vv = v ** 2
            vvv = v * vv
            r = vv * xz
            a = uu * zz - vvv - 2 * r
            x3 = v * a
            y3 = u * (r - a) - vvv * yz
            z3 = vvv * zz
            return x3, y3, z3

        def _dbl(x1, y1, z1):
            xx = x1 ** 2
            zz = z1 ** 2
            w = self.a * zz + 3 * xx
            s = 2 * y1 * z1
            ss = s ** 2
            sss = s * ss
            r = y1 * s
            rr = r ** 2
            b = (x1 + r) ** 2 - xx - rr
            h = w ** 2 - 2 * b
            x3 = h * s
            y3 = w * (b - h) - 2 * rr
            z3 = sss
            return x3, y3, z3
        r0 = (x, y, z)
        r1 = _dbl(x, y, z)
        for i in range(k.bit_length() - 2, -1, -1):
            if k & (1 << i):
                r0 = _add(*r0, *r1)
                r1 = _dbl(*r1)
            else:
                r1 = _add(*r0, *r1)
                r0 = _dbl(*r0)
        rx, ry, rz = r0
        rzi = ~rz
        return rx * rzi, ry * rzi

    def neg(self, x, y):
        return x, -y

    def field_size(self):
        return self.field.bit_length()

    def encode_point(self, point, compressed=False):
        byte_size = (self.field_size() + 7) // 8
        if not compressed:
            return bytes((0x04,)) + int(point.x).to_bytes(byte_size, byteorder="big") + int(
                    point.y).to_bytes(byte_size, byteorder="big")
        else:
            yp = int(point.y) & 1
            pc = bytes((0x02 | yp,))
            return pc + int(point.x).to_bytes(byte_size, byteorder="big")

    def decode_point(self, byte_data):
        if byte_data[0] == 0 and len(byte_data) == 1:
            return Inf(self)
        byte_size = (self.field_size() + 7) // 8
        if byte_data[0] in (0x04, 0x06):
            if len(byte_data) != 1 + byte_size * 2:
                raise ValueError("Wrong size for point encoding, should be {}, but is {}.".format(1 + byte_size * 2, len(byte_data)))
            x = Mod(int.from_bytes(byte_data[1:byte_size + 1], byteorder="big"), self.field)
            y = Mod(int.from_bytes(byte_data[byte_size + 1:], byteorder="big"), self.field)
            return Point(self, x, y)
        elif byte_data[0] in (0x02, 0x03):
            if len(byte_data) != 1 + byte_size:
                raise ValueError("Wrong size for point encoding, should be {}, but is {}.".format(1 + byte_size, len(byte_data)))
            x = Mod(int.from_bytes(byte_data[1:byte_size + 1], byteorder="big"), self.field)
            rhs = x ** 3 + self.a * x + self.b
            try:
                sqrt = rhs.sqrt()
            except ValueError:
                raise ValueError("Point not on curve.")
            yp = byte_data[0] & 1
            if int(sqrt) & 1 == yp:
                return Point(self, x, sqrt)
            else:
                return Point(self, x, self.field - sqrt)
        raise ValueError("Wrong encoding type: {}, should be one of 0x04, 0x06, 0x02, 0x03 or 0x00.".format(hex(byte_data[0])))

    def __str__(self):
        return "\"{}\": y^2 = x^3 + {}x + {} over {}".format(self.name, self.a, self.b, self.field)


class CurveF2m(Curve):
    def is_singular(self):
        return self.b == 0

    def on_curve(self, x, y):
        return (y ** 2 + x * y - x ** 3 - self.a * x ^ 2 - self.b) == 0

    def add(self, x1, y1, x2, y2):
        lm = (y1 + y2) / (x1 + x2)
        x3 = lm ** 2 + lm + x1 + x2 + self.a
        y3 = lm * (x1 + x3) + x3 + y1
        return x3, y3

    def dbl(self, x, y):
        lm = x + y / x
        x3 = lm ** 2 + lm + self.a
        y3 = x ** 2 + lm * x3 + x3
        return x3, y3

    def mul(self, k, x, y, z=1):
        def _add(x1, y1, z1, x2, y2, z2):
            a = x1 * z2
            b = x2 * z1
            c = a ** 2
            d = b ** 2
            e = a + b
            f = c + d
            g = y1 * (z2 ** 2)
            h = y2 * (z1 ** 2)
            i = g + h
            j = i * e
            z3 = f * z1 * z2
            x3 = a * (h + d) + b * (c + g)
            y3 = (a * j + f * g) * f + (j + z3) * x3
            return x3, y3, z3

        def _dbl(x1, y1, z1):
            a = x1 * z1
            b = x1 * x1
            c = b + y1
            d = a * c
            z3 = a * a
            x3 = c ** 2 + d + self.a * z3
            y3 = (z3 + d) * x3 + b ** 2 * z3
            return x3, y3, z3
        r0 = (x, y, z)
        r1 = _dbl(x, y, z)
        for i in range(k.bit_length() - 2, -1, -1):
            if k & (1 << i):
                r0 = _add(*r0, *r1)
                r1 = _dbl(*r1)
            else:
                r1 = _add(*r0, *r1)
                r0 = _dbl(*r0)
        rx, ry, rz = r0
        rzi = ~rz
        return rx * rzi, ry * (rzi ** 2)

    def neg(self, x, y):
        return x, x + y

    def field_size(self):
        return self.field.n

    def encode_point(self, point, compressed=False):
        byte_size = (self.field_size() + 7) // 8
        if not compressed:
            return bytes((0x04,)) + int(point.x).to_bytes(byte_size, byteorder="big") + int(
                    point.y).to_bytes(byte_size, byteorder="big")
        else:
            if int(point.x) == 0:
                yp = 0
            else:
                yp = int(point.y * point.x.inverse())
            pc = bytes((0x02 | yp,))
            return pc + int(point.x).to_bytes(byte_size, byteorder="big")

    def decode_point(self, byte_data):
        if byte_data[0] == 0 and len(byte_data) == 1:
            return Inf(self)
        byte_size = (self.field_size() + 7) // 8
        if byte_data[0] in (0x04, 0x06):
            if len(byte_data) != 1 + byte_size * 2:
                raise ValueError("Wrong size for point encoding, should be {}, but is {}.".format(1 + byte_size * 2, len(byte_data)))
            x = FElement(int.from_bytes(byte_data[1:byte_size + 1], byteorder="big"), self.field)
            y = FElement(int.from_bytes(byte_data[byte_size + 1:], byteorder="big"), self.field)
            return Point(self, x, y)
        elif byte_data[0] in (0x02, 0x03):
            if len(byte_data) != 1 + byte_size:
                raise ValueError("Wrong size for point encoding, should be {}, but is {}.".format(1 + byte_size, len(byte_data)))
            if self.field.n % 2 != 1:
                raise NotImplementedError
            x = FElement(int.from_bytes(byte_data[1:byte_size + 1], byteorder="big"), self.field)
            yp = byte_data[0] & 1
            if int(x) == 0:
                y = self.b ** (2 ** (self.field.n - 1))
            else:
                rhs = x + self.a + self.b * x ** (-2)
                z = rhs.half_trace()
                if z ** 2 + z != rhs:
                    raise ValueError
                if int(z) & 1 != yp:
                    z += 1
                y = x * z
            return Point(self, x, y)
        raise ValueError("Wrong encoding type: {}, should be one of 0x04, 0x06, 0x02, 0x03 or 0x00.".format(hex(byte_data[0])))

    def __str__(self):
        return "\"{}\" => y^2 + xy = x^3 + {}x^2 + {} over {}".format(self.name, self.a, self.b,
                                                                      self.field)


class SubGroup(object):
    def __init__(self, g, n, h):
        self.g = g
        self.n = n
        self.h = h

    def __eq__(self, other):
        if not isinstance(other, SubGroup):
            return False
        return self.g == other.g and self.n == other.n and self.h == other.h

    def __str__(self):
        return "Subgroup => generator {}, order: {}, cofactor: {}".format(self.g, self.n, self.h)

    def __repr__(self):
        return str(self)


class Inf(object):
    def __init__(self, curve, x=None, y=None):
        self.x = x
        self.y = y
        self.curve = curve

    def __eq__(self, other):
        if not isinstance(other, Inf):
            return False
        return self.curve == other.curve

    def __ne__(self, other):
        return not self.__eq__(other)

    def __neg__(self):
        return self

    def __add__(self, other):
        if isinstance(other, Inf):
            return Inf(self.curve)
        if isinstance(other, Point):
            return other
        raise TypeError(
                "Unsupported operand type(s) for +: '%s' and '%s'" % (self.__class__.__name__,
                                                                      other.__class__.__name__))

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        if isinstance(other, Inf):
            return Inf(self.curve)
        if isinstance(other, Point):
            return other
        raise TypeError(
                "Unsupported operand type(s) for +: '%s' and '%s'" % (self.__class__.__name__,
                                                                      other.__class__.__name__))

    def __str__(self):
        return "{} on {}".format(self.__class__.__name__, self.curve)

    def __repr__(self):
        return str(self)


class Point(object):
    def __init__(self, curve, x, y):
        self.curve = curve
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y and self.curve == other.curve

    def __ne__(self, other):
        return not self.__eq__(other)

    def __neg__(self):
        return Point(self.curve, *self.curve.neg(self.x, self.y))

    def __add__(self, other):
        if isinstance(other, Inf):
            return self
        if isinstance(other, Point):
            if self.curve != other.curve:
                raise ValueError("Cannot add points belonging to different curves")
            if self == -other:
                return Inf(self.curve)
            elif self == other:
                return Point(self.curve, *self.curve.dbl(self.x, self.y))
            else:
                return Point(self.curve, *self.curve.add(self.x, self.y, other.x, other.y))
        else:
            raise TypeError(
                    "Unsupported operand type(s) for +: '{}' and '{}'".format(
                            self.__class__.__name__,
                            other.__class__.__name__))

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return self - other

    def __mul__(self, other):
        if isinstance(other, int):
            if other % self.curve.group.n == 0:
                return Inf(self.curve)
            if other < 0:
                other = -other
                addend = -self
            else:
                addend = self
            if hasattr(self.curve, "mul") and callable(getattr(self.curve, "mul")):
                return Point(self.curve, *self.curve.mul(other, addend.x, addend.y))
            else:
                result = Inf(self.curve)
                # Iterate over all bits starting by the LSB
                for bit in reversed([int(i) for i in bin(abs(other))[2:]]):
                    if bit == 1:
                        result += addend
                    addend += addend
                return result
        else:
            raise TypeError(
                    "Unsupported operand type(s) for *: '%s' and '%s'" % (other.__class__.__name__,
                                                                          self.__class__.__name__))

    def __rmul__(self, other):
        return self * other

    def __str__(self):
        return "({}, {}) on {}".format(self.x, self.y, self.curve)

    def __repr__(self):
        return str(self)


def get_curve(name):
    if name in PRIME_FIELD:
        params = PRIME_FIELD[name]
        p = params["p"]
        g = (Mod(params["g"][0], p), Mod(params["g"][1], p))
        group = SubGroup(g, params["n"], params["h"])
        return CurveFp(p, Mod(params["a"], p), Mod(params["b"], p), group, name)
    elif name in BINARY_FIELD:
        params = BINARY_FIELD[name]
        field = FField(params["poly"][0], params["poly"])
        g = (FElement(params["g"][0], field), FElement(params["g"][1], field))
        group = SubGroup(g, params["n"], params["h"])
        return CurveF2m(field, FElement(params["a"], field), FElement(params["b"], field), group,
                        name)
    else:
        return None
