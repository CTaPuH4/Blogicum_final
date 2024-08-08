from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class OnlyAuthorMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user
