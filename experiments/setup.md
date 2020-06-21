# A log of the setup on Metacentrum

This is what it took to setup the libs, virt and stuff on [Metacentrum](https://metacentrum.cz/en/).

Important to do this on Skirit and other similar frontends **NOT Zuphux**.

```
module add python/3.8.0-gcc
module add gcc-8.3.0
module add autoconf automake libtool
python -m venv virt
. virt/bin/activate

mkdir libs

cd libs
wget https://gmplib.org/download/gmp/gmp-6.2.0.tar.xz
tar -xJvf gmp-6.2.0.tar.xz
wget https://www.mpfr.org/mpfr-current/mpfr-4.0.2.tar.gz
tar -xzvf mpfr-4.0.2.tar.gz
cd ..

cd libs/gmp-6.0.2
./configure --build=x86_64-pc-linux-gnu --prefix=/storage/brno3-cerit/home/j08ny/minerva/.local
make -j8
make install
cd ../..

cd libs/mpfr-6.0.2
./configure --build=x86_64-pc-linux-gnu --prefix=/storage/brno3-cerit/home/j08ny/minerva/.local --with-gmp=/storage/brno3-cerit/home/j08ny/minerva/.local
make -j8
make install
cd ../..

git clone https://github.com/fplll/fpylll
git clone https://github.com/fplll/g6k
cd fpylll
git clone https://github.com/fplll/fplll
cd ..

pip install Cython

cd fpylll/fplll
./autogen.sh
./configure --build=x86_64-pc-linux-gnu --prefix=/storage/brno3-cerit/home/j08ny/minerva/.local --with-gmp=/storage/brno3-cerit/home/j08ny/minerva/.local --with-mpfr=/storage/brno3-cerit/home/j08ny/minerva/.local --disable-static
make -j8
make install
cd ../..

cd fpylll
pip install -r requirements.txt
env CC="/software/gcc/8.3.0/bin/gcc" CXX="/software/gcc/8.3.0/bin/g++" CFLAGS="-I/storage/brno3-cerit/home/j08ny/minerva/.local/include -L/storage/brno3-cerit/home/j08ny/minerva/.local/lib" python setup.py build_ext
env CC="/software/gcc/8.3.0/bin/gcc" CXX="/software/gcc/8.3.0/bin/g++" CFLAGS="-I/storage/brno3-cerit/home/j08ny/minerva/.local/include -L/storage/brno3-cerit/home/j08ny/minerva/.local/lib" python setup.py install
cd ..

cd g6k
pip install -r requirements.txt
env CC="/software/gcc/8.3.0/bin/gcc" CXX="/software/gcc/8.3.0/bin/g++" CFLAGS="-I/storage/brno3-cerit/home/j08ny/minerva/.local/include -L/storage/brno3-cerit/home/j08ny/minerva/.local/lib" python setup.py build_ext
env CC="/software/gcc/8.3.0/bin/gcc" CXX="/software/gcc/8.3.0/bin/g++" CFLAGS="-I/storage/brno3-cerit/home/j08ny/minerva/.local/include -L/storage/brno3-cerit/home/j08ny/minerva/.local/lib" python setup.py install
cd ..
```