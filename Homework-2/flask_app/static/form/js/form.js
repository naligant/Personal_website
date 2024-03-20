// form variable
var form = document.getElementById("feedback_form");
// button variable
var display_button = document.getElementById("display_button")
// apply function when the button is clicked
display_button.onclick = function(){
    // toggle between flex and none when clicked
    if (form.style.display === "flex"){
        form.style.display = "none";
    }
    else{
        form.style.display = "flex";
    }
}
