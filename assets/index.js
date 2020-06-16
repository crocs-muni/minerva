var moved = false;

$(document).on("scroll", "", function (event) {
    console.log(event);
    moved = true;
});

$(document).on('click', '[data-toggle="lightbox"]', function (event) {
    event.preventDefault();
    var elem = $('<a class="figure-download" title="Download" aria-label="Download" href="' + $(this).attr("href") + '"><span class="fa-stack fa-lg"><i class="fas fa-circle fa-stack-2x" aria-hidden="true"></i><i class="fas fa-download fa-stack-1x fa-inverse" aria-hidden="true"></i></span></a>');
    $(this).ekkoLightbox({
        onShow: function (e) {
            $(e.target).find(".modal-body").append(elem);
        }
    });
});

$(document).on("show.bs.collapse", ".custom-collapsible", function (event) {
    $(event.target).siblings().first().find("i").toggleClass("fa-plus-square").toggleClass("fa-minus-square");
});

$(document).on("hide.bs.collapse", ".custom-collapsible", function (event) {
    $(event.target).siblings().first().find("i").toggleClass("fa-plus-square").toggleClass("fa-minus-square");
});

$(document).on("click", ".figure-link", function (event) {
    var id = $(event.target).attr("href");
    $(id).parents(".collapse").first().collapse("show");
    event.preventDefault();
    setTimeout(() => $(id).get(0).scrollIntoView({behavior: "smooth"}), 300);
});

function toc_display(hamburger) {
    hamburger.toggleClass('is-active');
    $('#navbar nav').slideToggle(100);
}

function toc_toggle() {
    $('#navbar').toggle();
    $('#toggle-toc-icon i:last-child').toggleClass('fa-chevron-right').toggleClass('fa-chevron-left');
    if (localStorage.getItem("toc-hidden") === "True") {
        localStorage.setItem("toc-hidden", "False");
    } else if (localStorage.getItem("toc-hidden") === "False" || !localStorage.getItem("toc-hidden")) {
        localStorage.setItem("toc-hidden", "True");
    }
}

function rot13(a) {
    return a.replace(/[a-zA-Z]/g, function (c) {
        return String.fromCharCode((c <= "Z" ? 90 : 122) >= (c = c.charCodeAt(0) + 13) ? c : c - 26);
    })
}

function setup() {
    $('[data-toggle="tooltip"]').tooltip();
    if (localStorage.getItem("toc-hidden") === "True") {
        $('#navbar').show();
        $('#toggle-toc-icon i:last-child').toggleClass('fa-chevron-right').toggleClass('fa-chevron-left');
    }
    if (window.matchMedia("(max-width: 991.98px)").matches) {
        $("#navbar").stickybits({useStickyClasses: true});
        $("#navbar nav a").on("click", "", function (event) {
            toc_display($("#menu"));
        });
    }
    let hrefs = document.getElementsByClassName("mail-href");
    for (let i = 0; i < hrefs.length; i++) {
        hrefs[i].href = rot13("znvygb:" + hrefs[i].dataset.rot13);
    }
    let elems = document.getElementsByClassName("mail-inner");
    for (let j = 0; j < elems.length; j++) {
        elems[j].innerHTML = rot13(elems[j].dataset.rot13);
    }
    let titles = [
        "Lattice attacks strike again",
        "ECDSA fragility in practice",
        "For loops leak",
        "The curse of ECDSA nonces",
        "Loop bounds leak",
        "Loop bounds are enough",
        "Leaky loops",
        "A ladder has no windows but can still leak",
        "Incomplete formulas leak everywhere"];
    document.title = "Minerva: " + titles[Math.floor(Math.random() * titles.length)];
    $(".pseudocode").each(function (index, elem) {
        let result = pseudocode.render($(elem).text(), null, {lineNumber: false, noEnd: true});
        $(result).addClass("pseudocode-render");
        $(result).attr("id", $(elem).attr("id"));
        $(elem).replaceWith(result);
    });
    setTimeout(() => {if (!moved) {$("#logo").get(0).scrollIntoView({behavior: "smooth"})}}, 3000);
}

window.addEventListener("load", setup);