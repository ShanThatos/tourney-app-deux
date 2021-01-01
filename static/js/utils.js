const checkRedirect = (res) => {
    if (res.hasOwnProperty("redirect"))
        window.location.href = res.redirect;
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
            let method = $(form).attr("method") || "POST";
            let onsuccess = $(form).attr("onsuccess") ? window[$(form).attr("onsuccess")] : checkRedirect;
            let osargs = $(form).attr("osargs") || "";
            if ($(form).attr("confirmDeleteMessage")) {
                Swal.fire({
                    icon: "question",
                    title: $(form).attr("confirmDeleteMessage"), 
                    showCancelButton: true, 
                    confirmButtonText: "Cancel",
                    cancelButtonText: "Delete",
                    cancelButtonColor: "red"
                }).then((result) => {
                    if (result.isConfirmed)
                        $(buttons).attr("disabled", false);    
                    else
                        sendAjax($(form).attr("action"), method, $(form).serialize(), buttons, $(form).find("input"), onsuccess, osargs);
                });
            } else
                sendAjax($(form).attr("action"), method, $(form).serialize(), buttons, $(form).find("input"), onsuccess, osargs);
        });
        $(form).removeAttr("enhance");
    });
}

function sendAjax(url, method, data, buttons, formInputs, onsuccess, osargs) {
    let enableButtons = () => {
        $(buttons).attr("disabled", false);
    };
    $.ajax({
        url: url, 
        method: method, 
        data: data
    })
    .done((res, status, xhr) => {
        if (res.status == "Success") {
            $(formInputs).val("");
            if (onsuccess) onsuccess(res, osargs);
        } else if (res.status == "Failure")
            showErrorMessage(res.message, enableButtons);
        else
            window.location = xhr.getResponseHeader("Current-URL");
        enableButtons();
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