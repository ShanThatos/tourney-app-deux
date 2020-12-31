const checkContinueURL = (res) => {
    if (res.hasOwnProperty("continueURL"))
        window.location.href = res.continueURL;
};

$(document).ready(() => {
    enhanceForms();
});

function enhanceForms() {
    $("form[enhance]").each((index, form) => {
        $(form).submit((e) => {
            let buttons = $(form).find("button[type='submit']");
            $(buttons).attr("disabled", true);
            e.preventDefault();
            sendPost($(form).attr("action"), $(form).serialize(), buttons, checkContinueURL);
        });
    });
}

function sendPost(url, data, buttons, onsuccess) {
    let enableButtons = () => {
        $(buttons).attr("disabled", false);
    };
    $.post(url, data)
    .done((res) => {1
        if (res.status == "Success") {
            if (onsuccess) onsuccess(res);
        } else showErrorMessage(res.message, enableButtons);
    })
    .fail(() => {
        showErrorMessage("An error occurred", enableButtons);
    });
}

function showErrorMessage(message, after) {
    Swal.fire("Error", message || "An error occurred", "error")
    .then(() => {
        if (after) after();
    });
}