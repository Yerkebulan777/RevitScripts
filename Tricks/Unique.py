def GetUniqueById(items):
    mmap, Iset = {}, []
    for item in items:
        try:
            if item.Id not in mmap:
                mmap[item.Id] = 1
                Iset.append(item)
        except:
            pass
    return Iset
