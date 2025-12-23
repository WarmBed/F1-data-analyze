// F1TV Token Extractor - Console Script
// 在 F1TV 頁面的開發者工具 Console 中執行此腳本
// 執行步驟:
// 1. 在瀏覽器中登入 F1TV (https://f1tv.formula1.com)
// 2. 按 F12 開啟開發者工具
// 3. 切換到 Console 分頁
// 4. 複製並貼上以下代碼，按 Enter 執行

(function() {
    // 尋找 login-session cookie
    var cookies = document.cookie.split(';');
    var loginSession = null;
    
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.startsWith('login-session=')) {
            loginSession = cookie.substring('login-session='.length);
            break;
        }
    }
    
    if (!loginSession) {
        alert('❌ Cookie "login-session" not found!\n\nPlease make sure you are logged in to F1TV.');
        return;
    }
    
    try {
        // URL 解碼
        var decoded = decodeURIComponent(loginSession);
        var data = JSON.parse(decoded);
        var token = data.data.subscriptionToken;
        
        if (!token) {
            alert('❌ Token not found in cookie data!');
            return;
        }
        
        // 顯示 token 給用戶複製
        var tokenDisplay = token.substring(0, 50) + '...' + token.substring(token.length - 20);
        
        console.log('='.repeat(60));
        console.log('F1TV Token Extracted Successfully!');
        console.log('='.repeat(60));
        console.log('Token length:', token.length);
        console.log('Token preview:', tokenDisplay);
        console.log('');
        console.log('Full token (copy this):');
        console.log(token);
        console.log('='.repeat(60));
        
        // 嘗試複製到剪貼板
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(token).then(function() {
                alert('✅ Token copied to clipboard!\n\nLength: ' + token.length + ' characters\n\nYou can now paste it in the F1T GUI.');
            }).catch(function() {
                prompt('✅ Token extracted! Copy it from here:', token);
            });
        } else {
            prompt('✅ Token extracted! Copy it from here:', token);
        }
        
    } catch (e) {
        console.error('Error parsing cookie:', e);
        alert('❌ Error parsing cookie:\n' + e.message);
    }
})();
