

document.addEventListener("DOMContentLoaded", () => {
            const toastElList = [].slice.call(document.querySelectorAll('.toast'))
            const toastList = toastElList.map(function (toastEl) {
                const toast = new bootstrap.Toast(toastEl, {delay: 5000})
                toast.show()
                return toast
            })
        })