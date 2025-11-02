console.log("✅ like_dislike_post.js loaded");

document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll('.post-like, .post-dislike');
    console.log("Found buttons:", buttons.length);

    buttons.forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();

            const postId = this.dataset.postId;
            const vote = this.classList.contains('post-like') ? 1 : -1;

            console.log("➡️ Sending fetch:", {postId, vote});

            fetch("/posts/api/post/like/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
                body: JSON.stringify({post_id: postId, vote: vote})
            })
                .then(response => {
                    console.log("📡 Response status:", response.status);
                    return response.json();
                })
                .then(data => {
                    console.log("📥 Received from Django:", data);

                    const likesSpan = document.querySelector(`#post-likes-${postId}`);
                    const dislikesSpan = document.querySelector(`#post-dislikes-${postId}`);

                    if (likesSpan) {
                        likesSpan.textContent = data.likes_count;
                    } else {
                        console.error(`⚠️ Element not found: #post-likes-${postId}`);
                    }

                    if (dislikesSpan) {
                        dislikesSpan.textContent = data.dislikes_count;
                    } else {
                        console.error(`⚠️ Element not found: #post-dislikes-${postId}`);
                    }
                })
                .catch(error => console.error("❌ Fetch error:", error));
        });
    });
});