const fs = require('fs');

const files = fs.readdirSync('.').filter(f => f.endsWith('.html'));
files.forEach(f => {
  let h = fs.readFileSync(f, 'utf8');
  h = h.replace(
    /<div class="header-tools">[\s\S]*?<\/div>/,
    `<div class="header-tools">
          <a class="utility-pill" href="wishlist.html" title="Wishlist"><i class="fa-regular fa-heart"></i></a>
          <a class="utility-pill cart-pill" href="cart.html" title="Cart"><i class="fa-sharp fa-solid fa-cart-shopping"></i><span class="cart-badge" data-cart-count>0</span></a>
          <a class="utility-pill" href="login.html" data-login-link title="Profile"><i class="fa-solid fa-user"></i></a>
        </div>`
  );
  fs.writeFileSync(f, h);
});
console.log('Update complete.');
