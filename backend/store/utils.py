def create_or_update_store(store, request):
    categories = request.data.get('categories')

    store.name = request.data.get('name')
    store.description = request.data.get('description')
    if categories:
        store.categories.clear()
        for category in categories:
            store.categories.add(category)
    store.save()

    return True


