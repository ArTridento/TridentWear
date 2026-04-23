const fs = require('fs');

const index = fs.readFileSync('index.html', 'utf8');
const headerMatch = index.match(/[\s\S]*?<main>/)[0];
const footerMatch = index.match(/<\/main>[\s\S]*/)[0];

const mainContent = `
      <section class="section">
        <div class="container" style="display: grid; grid-template-columns: 280px 1fr; gap: 2rem; align-items: start; padding-top: 2rem;">
          
          <!-- LEFT SIDEBAR -->
          <div class="profile-sidebar" style="display: flex; flex-direction: column; gap: 1rem;">
            
            <!-- User Info Box -->
            <div style="background: #f4f5f6; padding: 1.5rem; border-radius: var(--radius-sm);">
              <h3 id="sidebar-name" style="font-size: 1.1rem; margin-bottom: 0.2rem;">Hari Hara</h3>
              <p id="sidebar-email" style="font-size: 0.85rem; color: var(--gray-dark); margin-bottom: 0.5rem;">hari@example.com</p>
              <p id="sidebar-role" style="font-size: 0.8rem; color: #e03131;">(Member)</p>
            </div>

            <!-- Sidebar Nav Links -->
            <div style="display: flex; flex-direction: column; border: 1px solid #e9ecef; border-radius: var(--radius-sm);">
              <a href="#" style="padding: 1rem; border-bottom: 1px solid #e9ecef; display: flex; justify-content: space-between; color: var(--dark);">
                <span>Orders</span> <span style="color: var(--gray); font-size: 0.8rem;">(Track your order here)</span>
              </a>
              <a href="#" style="padding: 1rem; border-bottom: 1px solid #e9ecef; color: var(--dark);">Gift Vouchers</a>
              <a href="#" style="padding: 1rem; border-bottom: 1px solid #e9ecef; color: var(--dark);">
                Trident Points <span style="color: var(--primary); font-size: 0.8rem;">[Active Points: 0]</span>
              </a>
              <a href="#" style="padding: 1rem; border-bottom: 1px solid #e9ecef; color: var(--dark);">
                Trident Money <span style="color: var(--primary); font-size: 0.8rem;">[Wallet: ₹ 0.00]</span>
              </a>
              <a href="#" style="padding: 1rem; border-bottom: 1px solid #e9ecef; color: var(--dark);">FAQs</a>
              <a href="#" style="padding: 1rem; border-bottom: 1px solid #e9ecef; color: var(--primary); font-weight: 600;">Profile</a>
              <!-- membership -->
              <a href="#" style="padding: 1rem; color: #e03131;">My Membership</a>
            </div>

            <!-- Danger Buttons -->
            <div style="display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem;">
              <button class="btn btn-outline" style="color: #e03131; border-color: #e03131; border-radius: var(--radius-sm); font-weight: 700; width: 100%;">DELETE MY ACCOUNT</button>
              <button class="btn btn-outline" data-logout-button style="color: #e03131; border-color: #e03131; border-radius: var(--radius-sm); font-weight: 700; width: 100%;">LOGOUT</button>
            </div>

          </div>

          <!-- RIGHT CONTENT AREA -->
          <div class="profile-content">
            <h2 style="font-size: 1.1rem; color: var(--gray); font-weight: 600; margin-bottom: 1rem; text-transform: uppercase;">Edit Profile</h2>
            
            <div style="border: 1px solid #e9ecef; border-radius: var(--radius-sm); padding: 2rem;">
              
              <!-- Credentials Section -->
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2.5rem;">
                <div>
                  <label style="display: block; font-size: 0.9rem; font-weight: 500; color: var(--gray-dark); margin-bottom: 0.5rem;">Email Id</label>
                  <input type="email" id="profile-email-input" class="form-control" style="background: #f1f3f5; pointer-events: none;" readonly>
                </div>
                <div>
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <label style="font-size: 0.9rem; font-weight: 500; color: var(--gray-dark);">Password</label>
                    <a href="#" style="font-size: 0.85rem; color: var(--primary); font-weight: 500;">Change Password</a>
                  </div>
                  <input type="password" class="form-control" value="********" style="background: #f1f3f5; pointer-events: none;" readonly>
                </div>
              </div>

              <hr style="border: none; border-top: 1px solid #e9ecef; margin-bottom: 2rem;">

              <!-- General Info -->
              <h3 style="font-size: 1rem; color: var(--gray-dark); font-weight: 600; margin-bottom: 1.5rem;">General Information</h3>
              
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1.5rem;">
                <!-- Left Col -->
                <div style="display: grid; gap: 1.5rem;">
                  <div>
                    <label style="display: block; font-size: 0.9rem; font-weight: 500; color: var(--gray-dark); margin-bottom: 0.5rem;">First Name *</label>
                    <input type="text" id="profile-firstname" class="form-control" style="background: transparent;">
                  </div>
                  <div>
                    <label style="display: block; font-size: 0.9rem; font-weight: 500; color: var(--gray-dark); margin-bottom: 0.5rem;">Last Name</label>
                    <input type="text" id="profile-lastname" class="form-control" style="background: transparent;">
                  </div>
                  <div>
                    <label style="display: block; font-size: 0.9rem; font-weight: 500; color: var(--gray-dark); margin-bottom: 0.5rem;">Gender</label>
                    <div style="display: flex; gap: 1.5rem; margin-top: 0.5rem;">
                      <label style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.9rem; cursor: pointer;">
                        <input type="radio" name="gender" value="male" checked> Male
                      </label>
                      <label style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.9rem; cursor: pointer;">
                        <input type="radio" name="gender" value="female"> Female
                      </label>
                      <label style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.9rem; cursor: pointer;">
                        <input type="radio" name="gender" value="other"> Other
                      </label>
                    </div>
                  </div>
                </div>

                <!-- Right Col -->
                <div style="display: grid; gap: 1.5rem;">
                  <div>
                    <label style="display: block; font-size: 0.9rem; font-weight: 500; color: var(--gray-dark); margin-bottom: 0.5rem;">Date of Birth</label>
                    <input type="date" class="form-control" style="background: #f1f3f5;">
                  </div>
                  <div>
                    <label style="display: block; font-size: 0.9rem; font-weight: 500; color: var(--gray-dark); margin-bottom: 0.5rem;">Mobile Number *</label>
                    <input type="tel" class="form-control" style="background: transparent;">
                  </div>
                  <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                      <label style="font-size: 0.9rem; font-weight: 500; color: var(--gray-dark);">Default Address</label>
                      <a href="#" style="font-size: 0.85rem; color: var(--gray-dark); font-weight: 500;">Change/Edit</a>
                    </div>
                    <textarea class="form-control" rows="3" style="background: #e9ecef; pointer-events: none;" readonly>No Address Selected</textarea>
                  </div>
                </div>
              </div>

            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
              <button type="button" class="btn" style="background: #117864; color: #fff; font-weight: 700; padding: 0.85rem 3rem; border-radius: var(--radius-sm); border: none;">SAVE</button>
            </div>

          </div>
        </div>
      </section>
`;

fs.writeFileSync('profile.html', headerMatch + mainContent + footerMatch);
console.log('Done rendering layout onto profile.html');
