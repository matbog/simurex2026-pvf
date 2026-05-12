document.addEventListener("DOMContentLoaded", function () {

    const currentHost = window.location.hostname;

    document.querySelectorAll("a").forEach(link => {

        const url = new URL(link.href, window.location.origin);

        if (url.hostname !== currentHost) {

            link.setAttribute("target", "_blank");

            link.setAttribute("rel", "noopener noreferrer");
        }
    });
});