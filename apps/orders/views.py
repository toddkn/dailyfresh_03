import json

from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsSKU
from users.models import Address
from utils.views import LoginRequiredMixin, LoginRequiredJsonMixin


class PlaceOrdereView(View):
    def post(self, request):

        user = request.user

        # 前段页面要传输 数据

        # 1购物车点击提交过来  传过来 sku_ids
        # 2详情页面点击立即购买 传过来sku_ids 和count

        # 注意 id有多个传过来获取要用getlist 如果用get只能获取到最后一个
        sku_ids = request.POST.getlist('sku_ids')
        # 只有从详情页面点击立即购买 才会传count
        count = request.POST.get('count')

        # 下面的逻辑最后再写
        if not user.is_authenticated():
            response = redirect('/users/login?next=/cart')
            # 用户没有登录
            if count is not None:
                # 取出cookie里的数据
                cart_json = request.COOKIES.get('cart')
                # 如果cookie里有数据
                if cart_json:
                    cart_dict = json.loads(cart_json)
                else:
                    cart_dict = {}
                # {'id1':5,'id2':7}
                # 从立即购买页面进来 只有一个商品 取第0个
                sku_id = sku_ids[0]
                # 添加到字典里
                cart_dict[sku_id] = int(count)
                # 从定向到购物车
                if cart_dict:
                    response.set_cookie('cart', json.dumps(cart_dict))
            return response
        # 上面的逻辑最后再写


        # 校验参数
        if sku_ids is None:
            # 产品说的算 要进购物车 从立即购买过来的
            return redirect(reverse('cart:info'))

        # 收货地址 有user能查到
        # 获取商品的sku对象 skus
        # 每种商品的数量
        # 每种商品的数量总价
        # 所有的商品的数量
        # 所有的商品的总价
        # 运费10
        # 所有的商品的总价包括运费

        # 1收货地址 取最新的一个
        try:
            address = Address.objects.filter(user=user).latest('create_time')
        except:
            # 没有就是空 让用户去编辑
            address = None
        skus = []
        total_count = 0  # 所有的商品的数量
        total_sku_amount = 0  # 所有的商品的总价
        total_amount = 0  # 所有的商品的总价 包括运费
        trans_cost = 10  # 运费
        if count is None:
            # 从购物车过来的
            redis_conn = get_redis_connection('default')
            # {b'skuid1':b'10',b'skuid2':b'15'}
            cart_dict = redis_conn.hgetall('cart_%s' % user.id)
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    # 产品说的算 要进购物车
                    return redirect(reverse('cart:info'))
                # 注意sku_id要转换为字节型才能获取
                sku_count = cart_dict.get(sku_id.encode())
                sku_count = int(sku_count)  # 每种商品的数量
                sku_amount = sku_count * sku.price  # 每种商品的总价
                # 把信息存到sku对象里
                sku.count = sku_count
                sku.amount = sku_amount
                # 保存全部的sku
                skus.append(sku)
                total_count += sku_count  # 所有的商品的数量
                total_sku_amount += sku_amount  # 所有的商品的总价
        else:
            # 从详情页过来的   # 查商品数据
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    # 产品说的算 要进购物车
                    return redirect(reverse('cart:info'))
                # 强转数量
                try:
                    sku_count = int(count)  # 每种商品的数量
                    # href='{%url  'goods:detail'  1%}'
                    # http: // 127.0.0.1: 8000 / goods / detail / 12
                except Exception:
                    return redirect(reverse('goods:detail', args=sku_id))

                # 判断库存
                if sku_count > sku.stock:
                    return redirect(reverse('goods:detail', args=sku_id))

                sku_amount = sku_count * sku.price  # 每种商品的总价
                # 把数据存到sku对象里
                sku.count = sku_count
                sku.amount = sku_amount
                # 保存全部的sku
                skus.append(sku)
                total_count += sku_count  # 所有的商品的数量
                total_sku_amount += sku_amount  # 所有的商品的总价

        # 所有的商品的总价 包括运费
        total_amount = total_sku_amount + trans_cost

        context = {
            'skus': skus,
            'total_count': total_count,
            'total_sku_amount': total_sku_amount,
            'total_amount': total_amount,
            'trans_cost': trans_cost,
            'address': address
        }
        # 返回订单信息页面 注意还没有生成 提交后才生成
        return render(request, 'place_order.html', context)


# 提交订单的视图  用户有没有登录
class CommitOrderView(LoginRequiredJsonMixin,View):
    # 有大量数据传过来 用于生成订单 用post ajax请求

    def post(self, request):
        # 后端 只负责订单生成

        # if not request.user.is_authenticated():
        #     return JsonResponse({'code': 1, 'msg': '提交失败'})




        # 成功或者失败 要去做什么 由前端来做
        return JsonResponse({'code': 0, 'msg': '提交成功'})
