from rest_framework import serializers

from .models import CourseChannel, User


class CourseChannelSerializer(serializers.ModelSerializer):
    likes = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    def get_likes(self, obj: CourseChannel):
        return obj.likers.count()

    def get_is_liked(self, obj: CourseChannel):
        request = self.context.get("request")

        if request:
            user_id = request.GET.get("user_id")

            user = User.objects.filter(id=user_id)

            if user:
                user = user.first()

                return user in obj.likers.all()

        return False

    class Meta:
        model = CourseChannel
        fields = (
            "handle",
            "name",
            "logo",
            "likes",
            "is_liked",
        )
