from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from posts.models import Group, Post, User
from rest_framework import filters, permissions, status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CommentSerializer, FollowSerializer, GroupSerializer, PostSerializer)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def create(self, request, post_id=None):
        post = get_object_or_404(Post, pk=post_id)
        serializer = self.serializer_class(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(author=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        return post.comments.all()


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def create(self, request):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class FollowViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = FollowSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'following__username']

    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user.username)
        return user.follower

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
