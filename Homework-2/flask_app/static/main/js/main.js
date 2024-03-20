// form variable
var menu_icon = document.getElementById("menu_icon");
// button variable
var pulldown = document.getElementById("pulldown")
// apply function when the button is clicked
menu_icon.onclick = function(){
    // toggle between flex and none when clicked
    if (pulldown.style.display === "flex"){
        pulldown.style.display = "none";
    }
    else{
        pulldown.style.display = "flex";
    }
}

function checkWindow() {
    if (window.innerWidth > 650) {
        pulldown.style.display = "none";
    }
}
window.addEventListener('resize', checkWindow);
checkWindow();