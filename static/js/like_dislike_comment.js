console.log("✅ like_dislike_comment.js loaded");

document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll('.btn-like, .btn-dislike');
    console.log("Found buttons:", buttons.length);

    buttons.forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();

            const commentId = this.dataset.commentId;
            const vote = this.classList.contains('btn-like') ? 1 : -1;

            console.log("➡️ Sending fetch:", { commentId, vote });

            fetch("/posts/api/comment/like/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
                body: JSON.stringify({ comment_id: commentId, vote: vote })
            })
            .then(response => {
                console.log("📡 Response status:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("📥 Received from Django:", data);

                const likesSpan = document.querySelector(`#likes-${commentId}`);
                const dislikesSpan = document.querySelector(`#dislikes-${commentId}`);

                if (likesSpan) {
                    likesSpan.textContent = data.likes_count;
                } else {
                    console.error(`⚠️ Element not found: #likes-${commentId}`);
                }

                if (dislikesSpan) {
                    dislikesSpan.textContent = data.dislikes_count;
                } else {
                    console.error(`⚠️ Element not found: #dislikes-${commentId}`);
                }
            })
            .catch(error => console.error("❌ Fetch error:", error));
        });
    });
});