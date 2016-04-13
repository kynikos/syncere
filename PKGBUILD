# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

_projname=syncere
_authname=kynikos
pkgname=${_projname}-git
pkgver=0.1.0
pkgrel=1
pkgdesc='Interactive rsync-based data synchronization'
arch=('any')
url="https://github.com/${_authname}/${_projname}"
license=('GPL3')
depends=('python')
source=("git://github.com/${_authname}/${_projname}.git"
        "git://github.com/${_authname}/lib.py.forwarg.git")
md5sums=('SKIP'
         'SKIP')

pkgver() {
  cd $_projname
  echo $(git rev-list --count HEAD).$(git rev-parse --short HEAD)
}

package() {
    cd $_projname
    python setup.py install --root="$pkgdir" --optimize=1
}
