var originalSerializeArray = $.fn.serializeArray;
$.fn.extend({
    serializeArray: function () {
        var brokenSerialization = originalSerializeArray.apply(this);
        var checkboxValues = $(this).find('input[type=checkbox]').map(function () {
            return { 'name': this.name, 'value': this.checked };
        }).get();
        var checkboxKeys = $.map(checkboxValues, function (element) { return element.name; });
        var withoutCheckboxes = $.grep(brokenSerialization, function (element) {
            return $.inArray(element.name, checkboxKeys) == -1;
        });

        return $.merge(withoutCheckboxes, checkboxValues);
    }
});

const checkRedirect = (res) => {
    if (res.hasOwnProperty("redirect"))
        window.location.href = res.redirect;
};

$(document).ready(() => {
    enhanceForms();
    enhanceSelects();
    enhanceButtons();
});

function enhanceForms() {
    $("form[enhance]").each((index, form) => {
        $(form).submit((e) => {
            let buttons = $(form).find("button[type='submit']");
            $(buttons).attr("disabled", true);
            e.preventDefault();
            let method = $(form).attr("method") || "POST";
            let formInputs = $(form).attr("keepinputs") ? $() : $(form).find("input");
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
                        sendAjax($(form).attr("action"), method, $(form).serialize(), buttons, formInputs, onsuccess, osargs);
                });
            } else
                sendAjax($(form).attr("action"), method, $(form).serialize(), buttons, formInputs, onsuccess, osargs);
        });
        $(form).removeAttr("enhance");
    });
}

function enhanceSelects() {
    $("select.select2").each((index, select) => {
        $(select).select2();
        $(select).removeClass("select2");
    });
}

function enhanceButtons() {
    $("button[enhance]").each((index, button) => {
        $(button).click(() => {
            $(button).attr("disabled", true);
            let url = $(button).attr("url") || window.location.href;
            let method = $(button).attr("method");
            let data = JSON.parse($(button).attr("data"));
            let onsuccess = $(button).attr("onsuccess") ? window[$(button).attr("onsuccess")] : checkRedirect;
            let osargs = $(button).attr("osargs") || "";
            sendAjax(url, method, data, button, $(), onsuccess, osargs);
        });
        $(button).removeAttr("enhance");
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
            if (res.hasOwnProperty("message")) Swal.fire("Success", res.message, "success");
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